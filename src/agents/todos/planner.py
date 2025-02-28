from pathlib import Path

from lasagna import (
    build_simple_agent,
    build_standard_message_extractor,
)

from .my_model_binder import my_model_binder

def create_planner_agent():
    return my_model_binder()(
        build_simple_agent(
            name = 'planner',
            tools = [],
            message_extractor = build_standard_message_extractor(
                strip_tool_messages = False,
                extract_from_layered_agents = True,
                system_prompt_override="""
                    You're the planning expert. Use the pomodoro technique
                    to fill the allotted time.
                """.strip(),
            ),
            doc = "Use this tool to plan chunks of time."
        )
    )

__all__ = [
    'create_planner_agent',
]
