import uuid
from pathlib import Path
from datetime import datetime

from lasagna import (
    known_models,
    build_simple_agent,
    build_standard_message_extractor,
)

def archive_todo_document(doc_id: str) -> None:
    """
    Archive a todo document because it's complete and therefore no longer relevant.
    :param: doc_id: str: The ID of the todo document to archive.
    """
    print(f"[completer.py] Archiving todo document {doc_id=}...")
    doc_path = Path("local/archives/todos") / f"{doc_id}.txt"
    assert doc_path.exists()
    doc_path.unlink()
    print(f"[completer.py] Archived todo document: {doc_id}")

def create_todo_completer_agent():
    return known_models.BIND_ANTHROPIC_claude_35_sonnet()(
        build_simple_agent(
            name = 'todo_item_completer',
            tools = [archive_todo_document],
            message_extractor = build_standard_message_extractor(
                strip_tool_messages = False,
                extract_from_layered_agents = True,
                system_prompt_override="""
                    Your job is to archive completed todo items.
                """.strip(),
            ),
            doc = "Use this tool to archive completed todo items."
        )
    )

__all__ = [
    'create_todo_completer_agent',
]
