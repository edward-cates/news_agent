import json
import sys
import os
from datetime import datetime

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from twilio_phone_calls import (
    create_twilio_voice_response,
    TwilioPhoneCall,
)
from twilio_phone_calls.twilio_pydantic import StreamEventsEnum

from src.agent import Agent

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
        websocket_url="wss://6840-2605-a601-a314-f100-53fb-902-8792-1fc2.ngrok-free.app/stream",
    )
    response = Response(
        content=voice_response.to_xml(),
        media_type="application/xml",
    )
    return response

@app.websocket("/stream")
async def stream(websocket: WebSocket):
    try:
        await websocket.accept()
        print("Websocket opened.")
        sys.stdout.flush() # TODO: Is this needed?

        agent: Agent | None = None
        stream: TwilioPhoneCall | None = None

        async def _send_text_to_caller(text: str) -> None:
            assert stream is not None, "Stream not created."
            for response in stream.text__to__twilio_messages(text):
                await websocket.send_text(response)

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
                stream = TwilioPhoneCall.from_start_message(twilio_message)
                agent = Agent(phone_number=stream.caller)
                print(f"TwilioPhoneCall created: {stream.caller=}")
                await _send_text_to_caller("Hey! How can I help you?")
            else:
                """
                Voice samples are split across (very) many twilio messages.
                Once a full sample has been pieced together
                and a long pause detected, the voice message will be processed
                and a response (i.e. `mail`) provided.
                """
                stream.receive_twilio_message(twilio_message)
                mail: str | None = stream.check_mailbox()
                if mail is not None:
                    assert agent is not None, "Sanity check."
                    response: str = await agent.respond_to_caller(mail)
                    await _send_text_to_caller(response)
    except WebSocketDisconnect:
        print("Websocket closed.")
