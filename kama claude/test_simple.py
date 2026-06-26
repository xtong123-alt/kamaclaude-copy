import asyncio
import os
import sys
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from kamaclaude.core.llm import LLMProvider
from kamaclaude.core.tools import ToolRegistry
from kamaclaude.core.eventbus import EventBus
from kamaclaude.core.session import SessionManager
from kamaclaude.core.agent import Agent

load_dotenv()


async def main():
    print("Testing KamaClaude core components...")
    
    print("\n1. Initializing components...")
    llm = LLMProvider()
    tools = ToolRegistry()
    eventbus = EventBus()
    sessions = SessionManager()
    
    print("   [OK] LLMProvider initialized")
    print("   [OK] ToolRegistry initialized with tools:", [t.name for t in tools.get_all_tools()])
    print("   [OK] EventBus initialized")
    print("   [OK] SessionManager initialized")
    
    print("\n2. Creating session...")
    session = sessions.create_session()
    print(f"   [OK] Session created: {session.id}")
    
    print("\n3. Testing event bus...")
    events_received = []
    
    def on_event(evt):
        events_received.append(evt)
        print(f"   -> Event: {evt.type}")
    
    eventbus.subscribe_all(on_event)
    
    print("\n4. Creating agent...")
    agent = Agent(llm, tools, eventbus, sessions)
    print("   [OK] Agent created")
    
    print("\n[OK] All components initialized successfully!")
    print("\nTo run the full system:")
    print("  1. Start core: kama-core")
    print("  2. Start TUI:  kama-tui")


if __name__ == "__main__":
    asyncio.run(main())
