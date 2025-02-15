from pathlib import Path

from lasagna import (
    known_models,
    build_simple_agent,
    build_standard_message_extractor,
)

def create_planner_agent():
    return known_models.BIND_ANTHROPIC_claude_35_sonnet()(
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
