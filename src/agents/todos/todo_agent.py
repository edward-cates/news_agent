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
        current_date_and_time_pretty = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
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
                You are my personal assistant. You help me balance a reasonable workload
                with remembering what I'm supposed to do.

                Be minimally concise - I'm trying to conserve my LLM token budget. And use emojis.

                Start by getting todos summary and observer notes.

                When writing tasks, I don't need you to fill in the blanks and/or steps.
                Format the info I give you but don't make stuff up or guess.
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
