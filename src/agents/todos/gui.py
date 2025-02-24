from textual.app import App
from textual.widgets import Header, Footer, Input, Static
from textual.containers import ScrollableContainer

from .todo_agent import TodoAgent

class TodoApp(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #chat-container {
        height: 90%;
        width: 100%;
        border: solid green;
    }

    #message-input {
        dock: bottom;
        margin: 1 2;
    }
    """

    def compose(self):
        yield Header()
        with ScrollableContainer(id="chat-container"):
            yield Static(id="chat-log")
        yield Input(id="message-input", placeholder="Type your message...")
        yield Footer()

    def on_mount(self):
        self.agent = TodoAgent()
        self.query_one("#message-input").focus()

    async def on_input_submitted(self, message: Input.Submitted):
        input_widget = self.query_one("#message-input")
        chat_log = self.query_one("#chat-log")
        
        user_message = message.value

        chat_log.update(f"{chat_log.renderable}\nYou: {user_message}")
        input_widget.value = ""

        chat_log.update(f"{chat_log.renderable}\nAssistant: ")
        def print_next_token(token: str):
            chat_log.update(f"{chat_log.renderable}{token}")

        response = await self.agent.handle_human_message(user_message, print_next_token)
        # chat_log.update(f"{chat_log.renderable}\nAssistant: {response}")

