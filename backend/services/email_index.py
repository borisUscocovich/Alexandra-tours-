import json
import os
from typing import Optional

EMAIL_INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "email_index.json")

class EmailIndexService:
    def __init__(self):
        self._ensure_db()
        
    def _ensure_db(self):
        if not os.path.exists(os.path.dirname(EMAIL_INDEX_PATH)):
            os.makedirs(os.path.dirname(EMAIL_INDEX_PATH), exist_ok=True)
        if not os.path.exists(EMAIL_INDEX_PATH):
            with open(EMAIL_INDEX_PATH, "w") as f:
                json.dump({}, f)

    def _load(self) -> dict:
        try:
            with open(EMAIL_INDEX_PATH, "r") as f:
                return json.load(f)
        except:
            return {}

    def _save(self, data: dict):
        try:
            with open(EMAIL_INDEX_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving email index: {e}")

    def save_mapping(self, email: str, session_id: str):
        data = self._load()
        data[email] = session_id
        self._save(data)
        
    def get_session_id(self, email: str) -> Optional[str]:
        data = self._load()
        return data.get(email)

email_index = EmailIndexService()
