import asyncio
import sys
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

from kamaclaude.core.llm import LLMProvider
from kamaclaude.core.tools import ToolRegistry
from kamaclaude.core.eventbus import EventBus
from kamaclaude.core.session import SessionManager
from kamaclaude.core.agent import Agent


async def main():
    print("=" * 60)
    print("KamaClaude - 本地 AI Agent 系统")
    print("=" * 60)
    print()
    
    # 初始化组件
    print("[1/5] 初始化 LLM 提供者...")
    llm = LLMProvider()
    print(f"    ✓ API Key: {llm.api_key[:10]}...")
    print(f"    ✓ Base URL: {llm.base_url}")
    print(f"    ✓ Model: {llm.model}")
    
    print("[2/5] 初始化工具注册表...")
    tools = ToolRegistry()
    print(f"    ✓ 可用工具: {[t.name for t in tools.get_all_tools()]}")
    
    print("[3/5] 初始化事件总线...")
    eventbus = EventBus()
    
    print("[4/5] 初始化会话管理器...")
    sessions = SessionManager()
    
    print("[5/5] 初始化 Agent...")
    agent = Agent(llm, tools, eventbus, sessions)
    
    # 设置事件监听
    events = []
    def on_event(evt):
        events.append(evt)
        etype = evt.type.value
        data = evt.data
        
        if etype == "thought":
            print(f"  💭 {data.get('thought', '')}")
        elif etype == "tool_call":
            print(f"  🔧 {data.get('name', '')} {data.get('arguments', {})}")
        elif etype == "tool_result":
            content = data.get('content', '')[:100]
            if data.get('is_error'):
                print(f"  ✗ {content}...")
            else:
                print(f"  ✓ {content}...")
        elif etype == "run_complete":
            print(f"\n[完成] 状态: {data.get('status')}")
    
    eventbus.subscribe_all(on_event)
    
    # 创建会话
    session = sessions.create_session()
    print(f"\n会话 ID: {session.id}")
    
    # 简单测试
    print("\n" + "=" * 60)
    print("测试 1: 列出当前目录")
    print("=" * 60)
    
    try:
        # 发送任务
        goal = "列出当前目录下的所有文件和文件夹"
        print(f"\n任务: {goal}")
        
        run = await agent.run(session.id, goal)
        print(f"\n运行状态: {run.status}")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n\n运行出错: {e}")
        import traceback
        traceback.print_exc()
