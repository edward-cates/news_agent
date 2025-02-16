import uuid
from pathlib import Path
from datetime import datetime

from lasagna import (
    known_models,
    build_simple_agent,
    build_standard_message_extractor,
)

def create_todo_document(todo_document: str) -> None:
    """
    Save an atomic todo task document to disk with a unique ID.
    :param: todo_document: str: The full txt todo document body to save.
    """
    print("[creator.py] Saving todo document...")
    doc_id = uuid.uuid4().hex
    date_and_time_pretty = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_doc = f"id: {doc_id}\n\nCreated at: {date_and_time_pretty}\n\n{todo_document}"
    Path("local/archives/todos").mkdir(parents=True, exist_ok=True)
    with open(Path("local/archives/todos") / f"{doc_id}.txt", "w") as f:
        f.write(full_doc)
    print(f"[creator.py] Saved todo document: {doc_id}")

def create_todo_creator_agent():
    return known_models.BIND_ANTHROPIC_claude_35_sonnet()(
        build_simple_agent(
            name = 'todo_document_creator',
            tools = [create_todo_document],
            message_extractor = build_standard_message_extractor(
                strip_tool_messages = False,
                extract_from_layered_agents = True,
                system_prompt_override="""
                    Your job is to create atomic documents for every todo item.
                    If you need clarifying information to be able to track this task for me,
                    then ask - but not more than 2 questions per task.
                """.strip(),
            ),
            doc = "Use this tool to create a new todo document."
        )
    )

