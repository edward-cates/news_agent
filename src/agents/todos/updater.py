import traceback
import uuid
from pathlib import Path
from datetime import datetime
from typing import List

from lasagna import (
    Message,
    known_models,
    build_simple_agent,
    flat_messages,
    noop_callback,
    recursive_extract_messages,
    strip_tool_calls_and_results,
    override_system_prompt,
    Model,
    EventCallback,
    AgentRun,
)

from .my_model_binder import my_model_binder

from .summarizer import read_todos
from .archiver import archive_todo_document

def overwrite_todo_document(doc_id: str, todo_document: str) -> None:
    """
    Overwrite a todo document on disk.
    :param: doc_id: str: The ID of the todo document to update.
    :param: todo_document: str: The full txt todo document body to save.
    """
    print(f"[updater.py] Overwriting todo document {doc_id=}...")
    current_date_and_time_pretty = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    full_doc = f"id: {doc_id}\n\nRewritten at: {current_date_and_time_pretty}\n\n{todo_document}"
    doc_path = Path("local/archives/todos") / f"{doc_id}.txt"
    assert doc_path.exists()
    with open(doc_path, "w") as f:
        f.write(full_doc)
    print(f"[updater.py] Updated todo document: {doc_id}")

def append_to_todo_document(doc_id: str, todo_document: str) -> None:
    """
    Append text to a todo document on disk.
    :param: doc_id: str: The ID of the todo document to update.
    :param: todo_document: str: The text to append to the todo document.
    """
    print(f"[updater.py] Appending to todo document {doc_id=}...")
    current_date_and_time_pretty = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    full_doc = f"\n\nAppended at: {current_date_and_time_pretty}\n\n{todo_document}"
    doc_path = Path("local/archives/todos") / f"{doc_id}.txt"
    assert doc_path.exists()
    with open(doc_path, "a") as f:
        f.write(full_doc)
    print(f"[updater.py] Appended to todo document: {doc_id}")

SYSTEM_PROMPT = """
Follow the instructions by reading all current todos
and then making the appropriate modification.
""".strip()


class EditorAgent:
    """
    Use this agent to edit an existing todo document
    (but not archive).
    """

    def __init__(self):
        pass

    async def __call__(
        self,
        model: Model,
        event_callback: EventCallback,
        prev_runs: List[AgentRun],
    ) -> AgentRun:
        print("EDITOR AGENT")
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
                tools = [
                    overwrite_todo_document,
                    append_to_todo_document,
                ],
            )
            return flat_messages(
                agent_name = 'editor_agent',
                messages = new_messages,
            )
        except Exception as e:
            traceback.print_exc()
            raise e

