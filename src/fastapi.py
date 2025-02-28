import json
import sys
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, HTMLResponse, FileResponse, JSONResponse

# from twilio_phone_calls import (
#     create_twilio_voice_response,
#     TwilioPhoneCall,
# )
# from twilio_phone_calls.twilio_pydantic import StreamEventsEnum

# from src.agent import Agent
from src.agents.todos.todo_agent import TodoAgent

app = FastAPI()

start_time = datetime.now()


with open('local/.env.json', 'r') as f:
    env_vars = json.load(f)
    for key, value in env_vars.items():
        print(f"Writing {key=}")
        os.environ[key] = value

assert os.getenv("ANTHROPIC_API_KEY") != None

# hello world
@app.get("/")
async def root():
    print("Received hello world request")
    return {"message": f"Hello World {start_time}"}

@app.post("/")
async def phone_call(request: Request):
    print("Received phone call")
    form_data = await request.form()
    voice_response = create_twilio_voice_response(
        caller_number=form_data.get("Caller"),
        websocket_url=f"wss://{os.getenv('NGROK_URL')}/stream",
    )
    response = Response(
        content=voice_response.to_xml(),
        media_type="application/xml",
    )
    return response

@app.get("/todos/{todos_token}", response_class=HTMLResponse)
async def todos_page(todos_token: str):
    if todos_token != os.getenv("TODOS_TOKEN"):
        return Response(status_code=401)
    return FileResponse("src/web/todos.html")

@app.post("/todos/{todos_token}", response_class=JSONResponse)
async def todos_api(todos_token: str, request: Request):
    if todos_token != os.getenv("TODOS_TOKEN"):
        return Response(status_code=401)
    todos_dir = Path("local/archives/todos")
    todo_document_paths: list[Path] = list(todos_dir.glob('*.txt'))
    contents: list[dict] = []
    for file in todo_document_paths:
        doc_id: str = file.stem
        metadata_path: Path = todos_dir / f"{doc_id}.json"
        contents.append({
            "doc_id": doc_id,
            "metadata": json.loads(metadata_path.read_text()),
            "contents": file.read_text(),
        })
    return contents

@app.websocket("/todos")
async def todos(websocket: WebSocket):
    try:
        await websocket.accept()
        while True:
            message = await websocket.receive_text()
            now_pretty = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            todo_agent = TodoAgent()
            message = f"(User websocket message; Sent at {now_pretty}): {message}"
            response: str = await todo_agent.handle_human_message(message, callback=websocket.send_text)
            # await websocket.send_text(response)
    except WebSocketDisconnect:
        print("Websocket closed.")


@app.websocket("/stream")
async def stream(websocket: WebSocket):
    try:
        await websocket.accept()
        print("Websocket opened.")
        sys.stdout.flush() # TODO: Is this needed?

        agent: Agent | None = None
        stream: TwilioPhoneCall | None = None

        while True:
            twilio_json = await websocket.receive_text()
            twilio_message: dict = json.loads(twilio_json)

            if twilio_message["event"] == StreamEventsEnum.connected.value:
                print("Connected to Twilio.")
                continue

            if twilio_message["event"] == StreamEventsEnum.stop.value:
                print("The caller hung up.")
                if agent is not None:
                    await agent.end_call()
                break

            if stream is None:
                agent = Agent()
                stream = TwilioPhoneCall.from_start_message(
                    twilio_message,
                    send_websocket_message_async_method=websocket.send_text,
                    text_to_text_async_method=agent.respond_to_caller,
                )
                agent.set_phone_number(stream.caller)
                print(f"TwilioPhoneCall created: {stream.caller=}")
                await stream.send_text_as_audio("Hey! How can I help you?")
            else:
                """
                Voice samples are split across (very) many twilio messages.
                Once a full sample has been pieced together
                and a long pause detected, the voice message will be processed
                and a response (i.e. `mail`) provided.
                """
                await stream.receive_twilio_message(twilio_message)

    except WebSocketDisconnect:
        print("Websocket closed.")
        if agent is not None:
            await agent.end_call()
