import traceback
from pathlib import Path
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

from .summarizer import read_todos

SYSTEM_PROMPT = """
Prioritize tasks based on the user's instructions.
Group them by project.
List de-prioritized tasks in a bottom subsection.
Make it concise - one line per task.
Don't plan breaks or anything else non-task.
Use HTML for formatting (your HTML is rendered inside a message bubble).
""".strip()


class PlannerAgent:
    """
    Use this agent to write out a plan for accomplishing tasks.
    """

    def __init__(self):
        pass

    async def __call__(
        self,
        model: Model,
        event_callback: EventCallback,
        prev_runs: List[AgentRun],
    ) -> AgentRun:
        try:
            print("PLANNER AGENT")
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
                tools = [],
            )
            return flat_messages(
                agent_name = 'planner_agent',
                messages = new_messages,
            )
        except Exception as e:
            traceback.print_exc()
            raise e

