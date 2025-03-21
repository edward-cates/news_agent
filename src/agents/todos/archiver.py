import traceback
import shutil
from pathlib import Path
from datetime import datetime
from typing import List

from lasagna import (
    Message,
    Model,
    EventCallback,
    AgentRun,
    known_models,
    build_simple_agent,
    flat_messages,
    build_standard_message_extractor,
    recursive_extract_messages,
    strip_tool_calls_and_results,
    override_system_prompt,
)

from .summarizer import read_todos

def archive_todo_document(doc_id: str) -> None:
    """
    Archive a todo document because it's complete and therefore no longer relevant.
    :param: doc_id: str: The ID of the todo document to archive.
    """
    print(f"[archiver.py] Archiving todo document {doc_id=}...")
    doc_path = Path("local/archives/todos") / f"{doc_id}.txt"
    assert doc_path.exists()
    # move it to "local/archives/todos/archives"
    shutil.move(doc_path, Path("local/archives/todos/archives") / doc_path.name)
    json_path = Path("local/archives/todos") / f"{doc_id}.json"
    if json_path.exists():
        shutil.move(json_path, Path("local/archives/todos/archives") / json_path.name)
    print(f"[archiver.py] Archived todo document: {doc_id}")


SYSTEM_PROMPT = """
Your job is to archive todo items as told.
""".strip()


class ArchiverAgent:
    """
    Use this agent to archive todo documents.
    """
    def __init__(self):
        pass

    async def __call__(
        self,
        model: Model,
        event_callback: EventCallback,
        prev_runs: List[AgentRun],
    ) -> AgentRun:
        print("ARCHIVER AGENT")
        try:
            messages = recursive_extract_messages(
                prev_runs,
                from_layered_agents = False,
            )
            messages = strip_tool_calls_and_results(messages)
            messages = override_system_prompt(
                messages,
                "\n".join([
                    SYSTEM_PROMPT,
                    "Here are the remaining tasks:",
                    *read_todos(),
                ]),
            )
            new_messages: List[Message] = await model.run(
                event_callback = event_callback,
                messages = messages,
                tools = [archive_todo_document],
            )
            return flat_messages(
                agent_name = 'archiver_agent',
                messages = new_messages,
            )
        except Exception as e:
            traceback.print_exc()
            raise e

