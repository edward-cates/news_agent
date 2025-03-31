import traceback
import json
import uuid
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
    noop_callback,
    recursive_extract_messages,
    strip_tool_calls_and_results,
    override_system_prompt,
)
from .my_model_binder import my_model_binder

def _read_projects_json() -> dict:
    with open(Path("local/archives/todos/projects.json"), "r") as f:
        return json.load(f)

def create_todo_document(
    task_name: str,
    body_html: str,
    project_name: str,
    project_selection_reasoning: str,
    estimated_priority: int,
) -> None:
    """
    Save an atomic todo task document to disk with a unique ID.

    :param: task_name: str: The name of the task to save the todo document to.
    :param: body_html: str: The html body of the todo document.
    :param: project_name: str: The name of the project to save the todo document to.
    :param: project_selection_reasoning: str: The reasoning for selecting the project that was chosen.
    :param: estimated_priority: int: The estimated priority of the todo document, 1-3.
    """
    try:
        assert project_name in set(_read_projects_json().keys()), f"Project name {project_name} not found in projects.json"
        print(f"[creator.py] Project name: {project_name}")
        print(f"[creator.py] Project selection reasoning: {project_selection_reasoning}")
        print(f"[creator.py] Estimated priority: {estimated_priority}")
        print("[creator.py] Saving todo document...")
        doc_id = uuid.uuid4().hex
        current_date_and_time_pretty = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        full_doc = f"""<div class="todo-doc">
            <div class="todo-header">
                <div class="todo-id">ID: {doc_id}</div>
                <div class="todo-created">Created at: {current_date_and_time_pretty}</div>
                <div class="todo-project">Project: {project_name}</div>
                <div class="todo-priority">Priority: {estimated_priority}</div>
            </div>
            <div class="todo-title">{task_name}</div>
            <div class="todo-body">{body_html}</div>
        </div>"""
        Path("local/archives/todos").mkdir(parents=True, exist_ok=True)
        with open(Path("local/archives/todos") / f"{doc_id}.txt", "w") as f:
            f.write(full_doc)
        metadata = {
            "doc_id": doc_id,
            "task_name": task_name,
            "project_name": project_name,
            "project_selection_reasoning": project_selection_reasoning,
            "estimated_priority": estimated_priority,
        }
        metadata_path = Path("local/archives/todos") / f"{doc_id}.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)
        print(f"[creator.py] Saved todo document: {doc_id}")
    except Exception as e:
        traceback.print_exc()
        raise e

SYSTEM_PROMPT = f"""
Create an atomic todo document and choose a project to assign it to.
Make it short.
Projects to choose from:
{json.dumps(_read_projects_json())}
""".strip()

class CreatorAgent:
    """
    Use this agent to create a new todo documents.
    """

    def __init__(self):
        pass

    async def __call__(
        self,
        model: Model,
        event_callback: EventCallback,
        prev_runs: List[AgentRun],
    ) -> AgentRun:
        print("CREATOR AGENT")
        try:
            messages = recursive_extract_messages(
                prev_runs,
                from_layered_agents = False,
            )
            messages = strip_tool_calls_and_results(messages)
            messages = override_system_prompt(
                messages,
                SYSTEM_PROMPT,
            )
            new_messages: List[Message] = await model.run(
                event_callback = event_callback,
                messages = messages,
                tools = [
                    create_todo_document,
                ],
            )
            return flat_messages(
                agent_name = 'creator_agent',
                messages = new_messages,
            )
        except Exception as e:
            traceback.print_exc()
            raise e

