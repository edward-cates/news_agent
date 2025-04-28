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
from src.agents.todos.archiver import archive_todo_document
from src.agents.todos.updater import overwrite_todo_document

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

@app.post("/todos/archive/{task_id}/{todos_token}", response_class=JSONResponse)
async def archive_todo(task_id: str, todos_token: str):
    if todos_token != os.getenv("TODOS_TOKEN"):
        return Response(status_code=401)
    archive_todo_document(task_id)
    return {"message": "Todo archived"}

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

@app.post("/create_todo/{todos_token}", response_class=JSONResponse)
async def create_todo(todos_token: str, request: Request):
    if todos_token != os.getenv("TODOS_TOKEN"):
        return Response(status_code=401)
    data = await request.json()
    response: str = await call_todo_document_creator_agent(data["message"])
    return {"response": response}

@app.post("/edit_todo/{todos_token}", response_class=JSONResponse)
async def edit_todo(todos_token: str, request: Request):
    if todos_token != os.getenv("TODOS_TOKEN"):
        return Response(status_code=401)
    data = await request.json()
    response: str = await call_todo_document_updater_agent(data["message"])
    return {"response": response}

@app.post("/todos/update_priority/{task_id}/{new_priority}/{todos_token}", response_class=JSONResponse)
async def update_task_priority(task_id: str, new_priority: int, todos_token: str):
    if todos_token != os.getenv("TODOS_TOKEN"):
        return Response(status_code=401)
    
    # Read current metadata
    todos_dir = Path("local/archives/todos")
    metadata_path = todos_dir / f"{task_id}.json"
    if not metadata_path.exists():
        return Response(status_code=404)
    
    metadata = json.loads(metadata_path.read_text())
    
    # Update the task with new priority
    overwrite_todo_document(
        doc_id=task_id,
        task_name=metadata["task_name"],
        description=metadata["description"],
        estimated_priority=new_priority,
        time_sensitivity=metadata["time_sensitivity"],
        appended_notes=json.dumps(metadata["appended_notes"])
    )
    
    return {"message": "Priority updated successfully"}

@app.websocket("/todos/awfnq89h0n3984hn1098je0n9xf18n0398fn98n093jmf9")
async def todos(websocket: WebSocket):
    try:
        await websocket.accept()

        agent = TodoAgent(
            callback = websocket.send_text,
        )

        while True:
            message = await websocket.receive_text()
            now_pretty = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"(User websocket message; Sent at {now_pretty}): {message}"

            await agent.handle_human_message(message)
            print("Done processing request.")
            await websocket.send_text("<refresh>")
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
