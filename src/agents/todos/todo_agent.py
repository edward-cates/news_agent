import asyncio
import os
import json
from datetime import datetime
from typing import Callable

from lasagna import (
    Message,
    known_models,
    build_simple_agent,
    flat_messages,
    build_standard_message_extractor,
)

from src.agents.todos.creator import call_todo_document_creator_agent
from src.agents.todos.daily_plan_creator import TaskPlannerAgent
from src.agents.todos.summarizer import read_todos
from src.agents.todos.updater import call_todo_document_updater_agent
from src.agents.todos.archiver import archive_todo_document
from src.agents.todos.observer import overwrite_observer_notes, read_observer_notes

from .my_model_binder import my_model_binder

class TodoAgent:
    def __init__(self):
        self.messages: list[Message] = []

    async def handle_human_message(self, message: str, callback: Callable[[str], None]) -> str:
        async def payload_callback(event: dict):
            # https://github.com/Rhobota/lasagna-ai/blob/851c7f489d84596ec509dc48c3e21429da39714e/src/lasagna/tui.py#L24-L26
            if event[0] == 'ai' and event[1] == 'text_event':
                if asyncio.iscoroutinefunction(callback):
                    await callback(event[2])
                else:
                    callback(event[2])

        current_date_and_time_pretty = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        self.messages.append({
            'role': 'human',
            'text': f"(Sent at {current_date_and_time_pretty}) {message}",
        })
        agent = my_model_binder()(
            build_simple_agent(
                name = 'todo_agent',
                tools = [
                    call_todo_document_creator_agent,
                    TaskPlannerAgent(payload_callback),
                    call_todo_document_updater_agent,
                ],
                message_extractor = build_standard_message_extractor(
                    strip_tool_messages = False,
                    extract_from_layered_agents = False,
                )
            ),
        )

        agent_prompt = {
            'role': 'system',
            'text': f"""
                You are a task management assistant.
                Your job is to listen to the user's requests
                disseminate atomic instructions to task-specific agents.
                Atomic means every agent call works on a single todo document.
            """.strip(),
        }

        response = await agent(payload_callback, [
            flat_messages(
                agent_name = 'todo_agent',
                messages = [agent_prompt, *self.messages],
            ),
        ])
        assert response['type'] == 'messages'
        self.messages.extend(response['messages'])
        return response['messages'][-1]['text']
