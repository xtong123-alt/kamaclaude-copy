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
from kamaclaude.core.types import PermissionDecision
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


console = Console()


async def main():
    console.print(Panel(
        Text("欢迎使用 KamaClaude - 本地 AI Agent 系统", style="bold cyan"),
        subtitle="输入你的任务，Agent 会自动完成"
    ))
    
    # 初始化组件
    with console.status("[bold green]正在初始化..."):
        llm = LLMProvider()
        tools = ToolRegistry()
        eventbus = EventBus()
        sessions = SessionManager()
        agent = Agent(llm, tools, eventbus, sessions)
        
        # 简化演示：自动允许所有工具权限
        for tool in tools.get_all_tools():
            tools.allow_always(tool.name)
    
    console.print(f"\n[dim]LLM: {llm.model}[/dim]")
    console.print(f"[dim]Base URL: {llm.base_url}[/dim]")
    console.print(f"[dim]工具: {[t.name for t in tools.get_all_tools()]}[/dim]\n")
    
    # 创建会话
    session = sessions.create_session()
    console.print(f"[cyan]会话 ID: {session.id}[/cyan]\n")
    
    # 设置事件监听
    def on_event(evt):
        etype = evt.type.value
        data = evt.data
        
        if etype == "thought":
            console.print(f"  [dim]💭[/dim] {data.get('thought', '')}")
        elif etype == "tool_call":
            console.print(f"  [blue]🔧 {data.get('name', '')}[/blue] {data.get('arguments', {})}")
        elif etype == "tool_result":
            content = data.get('content', '')
            if data.get('is_error'):
                console.print(f"  [red]✗[/red] {content[:150]}...")
            else:
                console.print(f"  [green]✓[/green] {content[:150]}...")
        elif etype == "permission_request":
            # 已经自动允许了所有权限，这里不需要处理
            pass
        elif etype == "run_complete":
            status = data.get('status')
            if status == "completed":
                console.print("\n[bold green]✓ 任务完成[/bold green]")
            else:
                console.print(f"\n[bold red]✗ 失败: {data.get('error')}[/bold red]")
    
    eventbus.subscribe_all(on_event)
    
    console.print("\n[dim]输入任务开始，输入 'quit' 退出[/dim]\n")
    
    try:
        while True:
            task = console.input("[bold green]> [/bold green]")
            if task.lower() in ["quit", "exit", "q"]:
                console.print("\n再见！👋")
                break
            
            if not task.strip():
                continue
            
            console.print()
            with console.status("[bold yellow]Agent 正在工作..."):
                try:
                    await agent.run(session.id, task)
                except Exception as e:
                    console.print(f"[red]错误: {e}[/red]")
            
            console.print()
    
    except KeyboardInterrupt:
        console.print("\n\n再见！👋")
    except Exception as e:
        console.print(f"\n[red]出错: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(main())
