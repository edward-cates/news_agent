import json
from pathlib import Path

class Database:
    db_file_path: Path = Path('local/db.json')

    def __init__(self):
        if not self.db_file_path.exists():
            # write `{}`
            self.db_file_path.write_text('{}')

        self.db = json.loads(self.db_file_path.read_text())

    def read_user_preferences(self, phone_number: str) -> str:
        return self.db.get(phone_number, "")

    def write_user_preferences(self, phone_number: str, preferences: str):
        self.db[phone_number] = preferences
        self.db_file_path.write_text(json.dumps(self.db))
