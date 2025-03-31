from datetime import datetime
from typing import Callable, Awaitable

from lasagna import (
    AgentRun,
    Message,
    known_models,
    build_simple_agent,
    flat_messages,
    build_standard_message_extractor,
    EventPayload,
)

from src.agents.todos.creator import CreatorAgent
from src.agents.todos.daily_plan_creator import PlannerAgent
from src.agents.todos.summarizer import read_todos
from src.agents.todos.updater import EditorAgent
from src.agents.todos.archiver import ArchiverAgent
from src.agents.todos.observer import overwrite_observer_notes, read_observer_notes

from .my_model_binder import my_model_binder

SYSTEM_PROMPT = """
You are a task management assistant.
Your job is to listen to the user's requests
disseminate atomic instructions to task-specific agents.
Atomic means every agent call works on a single todo document.

The subagents will talk to the user, so you don't need to repeat what they say!
""".strip()


class TodoAgent:
    def __init__(self, callback: Callable[[str], Awaitable[None]]):
        self.runs: list[AgentRun] = [
            flat_messages(
                agent_name = 'todo_agent',
                messages = [
                    {
                        'role': 'system',
                        'text': SYSTEM_PROMPT,
                    },
                ],
            ),
        ]
        self.callback = callback

    async def payload_callback(self, event: EventPayload):
        # https://github.com/Rhobota/lasagna-ai/blob/851c7f489d84596ec509dc48c3e21429da39714e/src/lasagna/tui.py#L24-L26
        if event[0] == 'ai' and event[1] == 'text_event':
            await self.callback(event[2])

    async def handle_human_message(self, message: str) -> None:
        current_date_and_time_pretty = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

        self.runs.append(
            flat_messages(
                agent_name = 'todo_agent',
                messages = [
                    {
                        'role': 'human',
                        'text': f"(Sent at {current_date_and_time_pretty}) {message}",
                    },
                ],
            ),
        )

        agent = my_model_binder()(
            build_simple_agent(
                name = 'todo_agent',
                tools = [
                    read_todos,
                    PlannerAgent(),
                    ArchiverAgent(),
                    CreatorAgent(),
                    EditorAgent(),
                ],
            ),
        )

        response: AgentRun = await agent(self.payload_callback, self.runs)

        self.runs.append(response)

