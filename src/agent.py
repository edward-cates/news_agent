from lasagna import Message


from src.database import Database
from src.agents.news_agent import news_agent, _get_todays_headlines
from src.agents.user_preferences_agent import user_preferences_agent

class Agent:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.user_preferences: str = Database().read_user_preferences(phone_number)
        self.conversation_history: list[Message] = []
        self.todays_headlines: str = _get_todays_headlines()

    async def respond_to_caller(self, caller_message: str) -> str:
        print("Responding to caller...")
        self.conversation_history.append({
            'role': 'human',
            'text': caller_message,
        })
        response: list[Message] = await news_agent(
            user_preferences=self.user_preferences,
            todays_headlines=self.todays_headlines,
            history=self.conversation_history,
        )
        self.conversation_history.extend(response)

        print("Returning response.")
        response_text = response[-1]['text']
        print(response_text)
        return response_text

    async def end_call(self) -> None:
        print("Ending call...")
        user_preferences = await user_preferences_agent(
            user_preferences=self.user_preferences,
            history=self.conversation_history,
        )[-1]['text']
        Database().write_user_preferences(self.phone_number, user_preferences)
        print(f"Updated user preferences: {self.phone_number=} {user_preferences=}")

