from lasagna.types import (
    Message,
    ToolCall,
    ToolResult,
)

class ToolCallFilter:
    """
    Removes tool calls from message history.
    """
    def __init__(self, function_name: str) -> None:
        self.function_name = function_name
        self._call_ids_to_remove: set[str] = set()

    def filter(self, history: list[Message]) -> list[Message]:
        return [
            message for message in history
            if self._check_message(message)
        ]

    def _check_message(self, message: Message) -> bool:
        # Returns True to keep.
        if message['role'] == 'tool_call':
            return self._check_message_tool_call(message)
        if message['role'] == 'tool_res':
            return self._check_message_tool_result(message)
        return True

    def _check_message_tool_call(self, message: Message) -> bool:
        # Returns True to keep.
        return all([
            self._check_tool_call(tool_call)
            for tool_call in message['tools']
        ])

    def _check_message_tool_result(self, message: Message) -> bool:
        # Returns True to keep.
        return all([
            self._check_tool_result(tool_result)
            for tool_result in message['tools']
        ])

    def _check_tool_call(self, tool_call: ToolCall) -> bool:
        # Returns True to keep.
        if tool_call['function']['name'] == self.function_name:
            self._call_ids_to_remove.add(tool_call['call_id'])
            return False
        return True

    def _check_tool_result(self, tool_result: ToolResult) -> bool:
        # Returns True to keep.
        return tool_result['call_id'] not in self._call_ids_to_remove
