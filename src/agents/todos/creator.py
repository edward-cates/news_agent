import uuid
from pathlib import Path
from datetime import datetime

from lasagna import (
    build_simple_agent,
    flat_messages,
    noop_callback,
)
from .my_model_binder import my_model_binder

def create_todo_document(todo_document: str) -> None:
    """
    Save an atomic todo task document to disk with a unique ID.
    :param: todo_document: str: The full txt todo document body to save.
    """
    print("[creator.py] Saving todo document...")
    doc_id = uuid.uuid4().hex
    current_date_and_time_pretty = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    full_doc = f"id: {doc_id}\n\nCreated at: {current_date_and_time_pretty}\n\n{todo_document}"
    Path("local/archives/todos").mkdir(parents=True, exist_ok=True)
    with open(Path("local/archives/todos") / f"{doc_id}.txt", "w") as f:
        f.write(full_doc)
    print(f"[creator.py] Saved todo document: {doc_id}")

def create_todo_creator_agent():
    return my_model_binder()(
        build_simple_agent(
            name = 'todo_document_creator',
            tools = [create_todo_document],
            force_tool = True,
            max_tool_iters = 1,
        )
    )

async def call_todo_document_creator_agent(instructions: str) -> str:
    """
    Give the todo document creator agent instructions for a new todo document.

    :param: instructions: str: Brief instructions for the todo document.
    """
    agent = create_todo_creator_agent()
    messages = [
        {
            'role': 'system',
            'text': f"""
                Create an atomic todo document, which is a concise HTML card.
            """.strip(),
        },
        {
            'role': 'human',
            'text': instructions,
        },
    ]
    response = await agent(noop_callback, [
        flat_messages(
            agent_name = 'todo_document_creator',
            messages = messages,
        ),
    ])
    assert response['type'] == 'messages'
    return "done"
