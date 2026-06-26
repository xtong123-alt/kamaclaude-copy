import asyncio
import os
from dotenv import load_dotenv
from .agent import Agent
from .llm import LLMProvider
from .tools import ToolRegistry
from .eventbus import EventBus
from .session import SessionManager
from .ipc import IPCServer
from .types import Event, PermissionDecision

load_dotenv()


class KamaCore:
    def __init__(self):
        self.llm = LLMProvider()
        self.tools = ToolRegistry()
        self.eventbus = EventBus()
        self.sessions = SessionManager()
        self.agent = Agent(self.llm, self.tools, self.eventbus, self.sessions)
        
        host = os.getenv("KAMA_CORE_HOST", "127.0.0.1")
        port = int(os.getenv("KAMA_CORE_PORT", "7437"))
        self.ipc = IPCServer(host=host, port=port)
        
        self.current_session = None
        self._setup_handlers()
        self._setup_event_forwarding()
    
    def _setup_handlers(self):
        self.ipc.register_handler("create_session", self._handle_create_session)
        self.ipc.register_handler("get_session", self._handle_get_session)
        self.ipc.register_handler("run", self._handle_run)
        self.ipc.register_handler("permission", self._handle_permission)
        self.ipc.register_handler("get_events", self._handle_get_events)
    
    def _setup_event_forwarding(self):
        async def forward_event(event: Event):
            await self.ipc.broadcast(
                "event",
                {
                    "id": event.id,
                    "type": event.type,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data,
                    "session_id": event.session_id,
                    "run_id": event.run_id,
                    "step_id": event.step_id,
                },
            )
        
        self.eventbus.subscribe_all(forward_event)
    
    async def _handle_create_session(self, data: dict):
        session = self.sessions.create_session()
        self.current_session = session
        return {"session_id": session.id}
    
    async def _handle_get_session(self, data: dict):
        session_id = data.get("session_id")
        session = self.sessions.get_session(session_id)
        if session:
            return {
                "id": session.id,
                "created_at": session.created_at.isoformat(),
                "thread_length": len(session.thread),
            }
        return {"error": "Session not found"}
    
    async def _handle_run(self, data: dict):
        session_id = data.get("session_id")
        goal = data.get("goal", "")
        
        if not session_id:
            if not self.current_session:
                self.current_session = self.sessions.create_session()
            session_id = self.current_session.id
        
        asyncio.create_task(self.agent.run(session_id, goal))
        return {"session_id": session_id, "status": "started"}
    
    async def _handle_permission(self, data: dict):
        decision = data.get("decision")
        self.agent.respond_permission(PermissionDecision(decision))
        return {"status": "ok"}
    
    async def _handle_get_events(self, data: dict):
        session_id = data.get("session_id")
        run_id = data.get("run_id")
        events = self.eventbus.get_events(session_id=session_id, run_id=run_id)
        return {
            "events": [
                {
                    "id": e.id,
                    "type": e.type,
                    "timestamp": e.timestamp.isoformat(),
                    "data": e.data,
                }
                for e in events
            ]
        }
    
    async def start(self):
        await self.ipc.start()
        await asyncio.Future()


async def main():
    core = KamaCore()
    await core.start()


if __name__ == "__main__":
    asyncio.run(main())
