from pathlib import Path

from lasagna import (
    known_models,
    build_simple_agent,
    build_standard_message_extractor,
)

def overwrite_observer_notes(notes: str) -> list[str]:
    """
    Overwrite wholesale the observer notes file,
    which is where learnings about me (the user) are saved
    to help you (the assistant) help me more effectively.
    :param: notes: str: The notes to overwrite the observer notes file with.
    """
    print("[observer.py] Overwriting observer notes...")
    notes_path = Path("local/archives/observer_notes.txt")
    with open(notes_path, "w") as f:
        f.write(notes)
    print("[observer.py] Overwrote observer notes.")

def read_observer_notes() -> str:
    """
    Read the observer notes file and return the contents as a string.
    """
    print("[observer.py] Reading observer notes...")
    notes_path = Path("local/archives/observer_notes.txt")
    if not notes_path.exists():
        return "No observer notes found."
    return notes_path.read_text()

def create_observer_agent():
    return known_models.BIND_ANTHROPIC_claude_35_sonnet()(
        build_simple_agent(
            name = 'observer',
            tools = [
                overwrite_observer_notes,
                read_observer_notes,
            ],
            message_extractor = build_standard_message_extractor(
                strip_tool_messages = False,
                extract_from_layered_agents = True,
                system_prompt_override="""
                    Observations about me (the human user) help you serve me more
                    effectively. You can learn my tendencies and propose plans accordingly.
                """.strip(),
            ),
            doc = "Use this tool read and make notes about my behavior and preferences.",
        )
    )

__all__ = [
    'create_observer_agent',
]
