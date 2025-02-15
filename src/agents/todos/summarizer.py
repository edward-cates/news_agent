from pathlib import Path

from lasagna import (
    known_models,
    build_simple_agent,
    build_standard_message_extractor,
)

def read_todos() -> list[str]:
    """
    Read all todo txt documents and returns them as a list of strings.
    """
    print("Reading todos...")
    todos_dir = Path("local/archives/todos")
    todos_files = todos_dir.glob("*.txt")
    return [
        todo_file.read_text()
        for todo_file in todos_files
    ]

def create_summarizer_agent():
    return known_models.BIND_ANTHROPIC_claude_35_sonnet()(
        build_simple_agent(
            name = 'summarizer',
            tools = [read_todos],
            message_extractor = build_standard_message_extractor(
                strip_tool_messages = False,
                extract_from_layered_agents = True,
                system_prompt_override="""
                    You are my personal assistant. You keep my head attached.
                    I focus hard on the current moment and forget what I'm supposed to do.
                    You are attentive to detail and prevent things from falling through the cracks.
                """.strip(),
            ),
            doc = "Use this tool to tell me what I need to do."
        )
    )

__all__ = [
    'create_summarizer_agent',
]
