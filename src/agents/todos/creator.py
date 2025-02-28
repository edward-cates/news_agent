import json
import uuid
from pathlib import Path
from datetime import datetime

from lasagna import (
    build_simple_agent,
    flat_messages,
    noop_callback,
)
from .my_model_binder import my_model_binder

def _read_projects_json() -> dict:
    with open(Path("local/archives/todos/projects.json"), "r") as f:
        return json.load(f)

def create_todo_document(
    todo_document: str,
    project_name: str,
    project_selection_reasoning: str,
    estimated_priority: int,
) -> None:
    """
    Save an atomic todo task document to disk with a unique ID.
    :param: todo_document: str: The full txt todo document body to save.
    :param: project_name: str: The name of the project to save the todo document to.
    :param: project_selection_reasoning: str: The reasoning for selecting the project that was chosen.
    :param: estimated_priority: int: The estimated priority of the todo document, 1-3.
    """
    assert project_name in set(_read_projects_json().keys()), f"Project name {project_name} not found in projects.json"
    print(f"[creator.py] Project name: {project_name}")
    print(f"[creator.py] Project selection reasoning: {project_selection_reasoning}")
    print(f"[creator.py] Estimated priority: {estimated_priority}")
    print("[creator.py] Saving todo document...")
    doc_id = uuid.uuid4().hex
    current_date_and_time_pretty = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    full_doc = f"id: {doc_id}\n\nCreated at: {current_date_and_time_pretty}\n\n{todo_document}"
    Path("local/archives/todos").mkdir(parents=True, exist_ok=True)
    with open(Path("local/archives/todos") / f"{doc_id}.txt", "w") as f:
        f.write(full_doc)
    metadata = {
        "doc_id": doc_id,
        "project_name": project_name,
        "project_selection_reasoning": project_selection_reasoning,
        "estimated_priority": estimated_priority,
    }
    metadata_path = Path("local/archives/todos") / f"{doc_id}.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)
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

                Projects to choose from:
                {json.dumps(_read_projects_json())}
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
