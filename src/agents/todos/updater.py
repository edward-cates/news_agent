import uuid
from pathlib import Path
from datetime import datetime

from lasagna import (
    known_models,
    build_simple_agent,
    build_standard_message_extractor,
)

def overwrite_todo_document(doc_id: str, todo_document: str) -> None:
    """
    Overwrite a todo document on disk.
    :param: doc_id: str: The ID of the todo document to update.
    :param: todo_document: str: The full txt todo document body to save.
    """
    print(f"Overwriting todo document {doc_id=}...")
    date_and_time_pretty = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_doc = f"id: {doc_id}\n\nRewritten at: {date_and_time_pretty}\n\n{todo_document}"
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
    print(f"Appending to todo document {doc_id=}...")
    date_and_time_pretty = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_doc = f"\n\nAppended at: {date_and_time_pretty}\n\n{todo_document}"
    doc_path = Path("local/archives/todos") / f"{doc_id}.txt"
    assert doc_path.exists()
    with open(doc_path, "a") as f:
        f.write(full_doc)
    print(f"[updater.py] Appended to todo document: {doc_id}")

def create_todo_updater_agent():
    return known_models.BIND_ANTHROPIC_claude_35_sonnet()(
        build_simple_agent(
            name = 'todo_document_updater',
            tools = [overwrite_todo_document],
            message_extractor = build_standard_message_extractor(
                strip_tool_messages = False,
                extract_from_layered_agents = True,
                system_prompt_override="""
                    Sometimes we don't get todo documents perfect on the first try.
                    Your job is to help me fix them, whether that means overwriting a bad doc
                    wholesale or asking up to 2 clarifying questions to append.
                """.strip(),
            ),
            doc = "Use this tool to update (overwrite or append) an existing todo document."
        )
    )

__all__ = [
    'create_todo_updater_agent',
]
