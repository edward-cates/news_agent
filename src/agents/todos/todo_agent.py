import traceback
import asyncio
import os
import json
from datetime import datetime

from lasagna import (
    Message,
    known_models,
    build_simple_agent,
    noop_callback,
    flat_messages,
    build_standard_message_extractor,
)

from src.agents.todos.creator import create_todo_document
from src.agents.todos.summarizer import read_todos
from src.agents.todos.updater import overwrite_todo_document, append_to_todo_document
from src.agents.todos.archiver import archive_todo_document
from src.agents.todos.observer import overwrite_observer_notes, read_observer_notes

class TodoAgent:
    def __init__(self):
        self.messages: list[Message] = []

    async def handle_human_message(self, message: str) -> str:
        current_date_and_time_pretty = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.messages.append({
            'role': 'human',
            'text': f"(Sent at {current_date_and_time_pretty}) {message}",
        })
        agent = known_models.BIND_ANTHROPIC_claude_35_sonnet()(
            build_simple_agent(
                name = 'todo_agent',
                tools = [
                    create_todo_document,
                    read_todos,
                    overwrite_todo_document,
                    append_to_todo_document,
                    archive_todo_document,
                    overwrite_observer_notes,
                    read_observer_notes,
                ],
                message_extractor = build_standard_message_extractor(
                    strip_tool_messages = False,
                    extract_from_layered_agents = True,
                )
            ),
        )
        agent_prompt = {
            'role': 'system',
            'text': f"""
                You are my personal assistant. You keep my head attached.
                I focus hard on the current moment and forget what I'm supposed to do.
                You are attentive to detail and prevent things from falling through the cracks.

                When completing daily tasks, append a timestamped line rather than archiving.

                Always start by getting todos summary and observer notes.
            """.strip(),
        }
        response = await agent(noop_callback, [
            flat_messages(
                agent_name = 'todo_agent',
                messages = [agent_prompt, *self.messages],
            ),
        ])
        assert response['type'] == 'messages'
        self.messages.extend(response['messages'])
        return response['messages'][-1]['text']


async def main():
    with open('local/.env.json', 'r') as f:
        env_vars = json.load(f)
        for key, value in env_vars.items():
            print(f"Writing {key=}")
            os.environ[key] = value

    agent = TodoAgent()
    while True:
        try:
            current_date_and_time_pretty = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = input(f"Enter a message (Sent at {current_date_and_time_pretty}): ")
            response = await agent.handle_human_message(message)
            print(response)
        except KeyboardInterrupt:
            break
        except Exception as e:
            traceback.print_exc()
            print("An error occurred. Please try again.")


if __name__ == '__main__':
    asyncio.run(main())
