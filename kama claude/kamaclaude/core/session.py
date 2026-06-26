import os
import json
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
from .types import Session, Run, Message
from dotenv import load_dotenv

load_dotenv()


class SessionManager:
    def __init__(self):
        data_dir = os.getenv("KAMA_DATA_DIR", "./.kama")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir = self.data_dir / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        self.sessions: Dict[str, Session] = {}
        self._load_sessions()
    
    def _load_sessions(self):
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    session = Session(**data)
                    self.sessions[session.id] = session
            except Exception as e:
                print(f"Error loading session {session_file}: {e}")
    
    def create_session(self) -> Session:
        import uuid
        session_id = f"sess-{uuid.uuid4().hex[:12]}"
        session = Session(id=session_id)
        self.sessions[session.id] = session
        self._save_session(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, message: Message):
        session = self.get_session(session_id)
        if session:
            session.thread.append(message)
            session.updated_at = datetime.now()
            self._save_session(session)
    
    def save_run(self, run: Run):
        session = self.get_session(run.session_id)
        if session:
            session.updated_at = datetime.now()
            self._save_session(session)
    
    def _save_session(self, session: Session):
        session_file = self.sessions_dir / f"{session.id}.json"
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.model_dump(), f, default=str, indent=2)
