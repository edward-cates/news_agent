from pathlib import Path

from lasagna import (
    known_models,
    build_simple_agent,
    flat_messages,
    noop_callback,
)

from .my_model_binder import my_model_binder

from .summarizer import read_todos

class TaskPlannerAgent:
    def __init__(self, callback):
        self.callback = callback

    async def __call__(self, instructions: str) -> str:
        """
        Call the task planner agent to create a plan for tasks as specified by the instructions.

        :param: instructions: str: Instructions for the task planner agent.
        """
        agent = my_model_binder()(
            build_simple_agent(
                name = 'task_planner',
                tools = [read_todos],
                # force_tool = True,
                # max_tool_iters = 1,
            )
        )
        messages = [
            {
                'role': 'system',
                'text': f"""
                    Prioritize tasks based on the user's instructions.
                    Always list all remaining tasks in a bottom subsection.
                    Make it concise.
                    Use HTML for formatting.
                """,
            },
            {
                'role': 'human',
                'text': instructions,
            }
        ]
        response = await agent(self.callback, [
            flat_messages(
                agent_name = 'task_planner',
                messages = messages,
            ),
        ])
        assert response['type'] == 'messages'
        return "done"
