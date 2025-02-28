import uuid
from pathlib import Path
from datetime import datetime

from lasagna import (
    known_models,
    build_simple_agent,
    flat_messages,
    noop_callback,
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

async def call_todo_document_updater_agent(instructions: str) -> str:
    """
    Give the todo document updater agent instructions for any type of
    modification to an existing todo document.

    :param: instructions: str: Brief instructions for the todo document.
    """
    print(f"[updater.py] Calling todo document updater agent with instructions: {instructions}")
    agent = my_model_binder()(
        build_simple_agent(
            name = 'todo_document_updater',
            tools = [
                overwrite_todo_document,
                append_to_todo_document,
                archive_todo_document,
            ],
            force_tool = True,
            max_tool_iters = 1,
        )
    )
    messages = [
        {
            'role': 'system',
            'text': f"""
                Follow the instructions by reading all current todos
                and then making the appropriate modification.

                Current tasks:
                {read_todos()}
            """,
        },
        {
            'role': 'human',
            'text': instructions,
        },
    ]
    response = await agent(noop_callback, [
        flat_messages(
            agent_name = 'todo_document_updater',
            messages = messages,
        ),
    ])
    assert response['type'] == 'messages'
    return "done"

__all__ = [
    'call_todo_document_updater_agent',
]
