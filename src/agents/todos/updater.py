import traceback
from pathlib import Path
from datetime import datetime
from typing import List
import json

from lasagna import (
    Message,
    flat_messages,
    recursive_extract_messages,
    strip_tool_calls_and_results,
    override_system_prompt,
    Model,
    EventCallback,
    AgentRun,
)

from .summarizer import read_todos

def overwrite_todo_document(
    doc_id: str,
    task_name: str,
    body_html: str,
    estimated_priority: int,
    appended_notes: str,
) -> None:
    """
    Overwrite a todo document on disk.

    :param: doc_id: str: The ID of the todo document to update.
    :param: task_name: str: The name of the task to save the todo document to.
    :param: body_html: str: The html body of the todo document.
    :param: estimated_priority: int: The estimated priority of the todo document (1-3).
    :param: appended_notes: str: A JSON list of string notes to append to the todo document.
    """
    print(f"[updater.py] Overwriting todo document {doc_id=}...")

    doc_path = Path("local/archives/todos") / f"{doc_id}.txt"
    assert doc_path.exists()

    metadata = json.load(open(doc_path.with_suffix(".json")))
    project_name = metadata["project_name"]

    current_date_and_time_pretty = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    appended_notes_html = '\n'.join([
        f"<li class='todo-note'>{note}</li>" 
        for note in json.loads(appended_notes)
    ])
    full_doc = f"""<div class="todo-doc">
        <div class="todo-header">
            <div class="todo-id">ID: {doc_id}</div>
            <div class="todo-created">Created at: {current_date_and_time_pretty}</div>
            <div class="todo-project">Project: {project_name}</div>
            <div class="todo-priority">Priority: {estimated_priority}</div>
        </div>
        <div class="todo-title">{task_name}</div>
        <div class="todo-body">{body_html}</div>
        <div class="todo-footer">
            <ul>
                {appended_notes_html}
            </ul>
        </div>
    </div>"""
    with open(doc_path, "w") as f:
        f.write(full_doc)
    print(f"[updater.py] Updated todo document: {doc_id}")


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
                ],
            )
            return flat_messages(
                agent_name = 'editor_agent',
                messages = new_messages,
            )
        except Exception as e:
            traceback.print_exc()
            raise e

