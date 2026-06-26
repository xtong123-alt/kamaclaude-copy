import asyncio
from typing import Dict, List, Callable, Any
from .types import Event, EventType


class EventBus:
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable[[Event], Any]]] = {}
        self.all_subscribers: List[Callable[[Event], Any]] = []
        self.events: List[Event] = []
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], Any]):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def subscribe_all(self, callback: Callable[[Event], Any]):
        self.all_subscribers.append(callback)
    
    async def emit(self, event: Event):
        self.events.append(event)
        
        for callback in self.all_subscribers:
            asyncio.create_task(self._safe_call(callback, event))
        
        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                asyncio.create_task(self._safe_call(callback, event))
    
    async def _safe_call(self, callback: Callable[[Event], Any], event: Event):
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            print(f"Error in event callback: {e}")
    
    def get_events(self, session_id: str = None, run_id: str = None) -> List[Event]:
        events = self.events
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        if run_id:
            events = [e for e in events if e.run_id == run_id]
        return events
