import asyncio
import sys
import os
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def check_env():
    """检查环境配置"""
    console.print("\n[bold cyan]1. 检查配置文件...[/]")
    
    env_file = ".env"
    if not os.path.exists(env_file):
        console.print(f"  [red]✗ {env_file} 不存在[/]")
        return False
    
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_api_key = "ALIYUN_API_KEY" in content and "your_api_key" not in content
    if has_api_key:
        console.print("  [green]✓ API Key 已配置[/]")
    else:
        console.print("  [yellow]⚠ API Key 可能未正确配置[/]")
    
    return True


def check_imports():
    """检查模块导入"""
    console.print("\n[bold cyan]2. 检查核心模块...[/]")
    
    try:
        from kamaclaude.core.llm import LLMProvider
        from kamaclaude.core.tools import ToolRegistry
        from kamaclaude.core.eventbus import EventBus
        from kamaclaude.core.session import SessionManager
        from kamaclaude.core.agent import Agent
        console.print("  [green]✓ 所有核心模块导入成功[/]")
        return True
    except Exception as e:
        console.print(f"  [red]✗ 导入失败: {e}[/]")
        return False


async def test_agent():
    """测试 Agent 核心功能"""
    console.print("\n[bold cyan]3. 测试 Agent 功能...[/]")
    
    try:
        from kamaclaude.core.llm import LLMProvider
        from kamaclaude.core.tools import ToolRegistry
        from kamaclaude.core.eventbus import EventBus
        from kamaclaude.core.session import SessionManager
        from kamaclaude.core.agent import Agent
        
        # 初始化
        llm = LLMProvider()
        console.print(f"    [dim]→ LLM: {llm.model}[/]")
        
        tools = ToolRegistry()
        console.print(f"    [dim]→ 工具: {[t.name for t in tools.get_all_tools()]}[/]")
        
        eventbus = EventBus()
        sessions = SessionManager()
        
        agent = Agent(llm, tools, eventbus, sessions)
        
        # 自动允许权限
        for tool in tools.get_all_tools():
            tools.allow_always(tool.name)
        
        # 创建会话
        session = sessions.create_session()
        console.print(f"    [dim]→ 会话: {session.id}[/]")
        
        # 测试简单任务
        console.print("    [dim]→ 执行简单测试任务...[/]")
        
        # 收集事件
        events = []
        def collect_events(evt):
            events.append(evt)
        
        eventbus.subscribe_all(collect_events)
        
        # 执行一个简单任务
        await agent.run(session.id, "列出当前目录的文件")
        
        console.print("  [green]✓ Agent 运行成功[/]")
        return True
        
    except Exception as e:
        console.print(f"  [red]✗ Agent 测试失败: {e}[/]")
        import traceback
        traceback.print_exc()
        return False


def check_ui_files():
    """检查界面文件"""
    console.print("\n[bold cyan]4. 检查界面文件...[/]")
    
    ui_files = ["simple_tui.py", "simple_cli.py", "kamaclaude_tui.py"]
    all_exist = True
    
    for f in ui_files:
        if os.path.exists(f):
            console.print(f"  [green]✓ {f}[/]")
        else:
            console.print(f"  [red]✗ {f} 不存在[/]")
            all_exist = False
    
    return all_exist


def print_summary(success):
    """打印总结"""
    if success:
        console.print(Panel(
            Text.assemble(
                ("\n🎉 KamaClaude 验证通过！\n\n", "bold green"),
                ("你现在可以运行:\n", "white"),
                ("  python simple_tui.py\n", "bold cyan"),
                ("\n来启动美观的 TUI 界面！\n", "dim")
            ),
            title="验证成功",
            border_style="green"
        ))
    else:
        console.print(Panel(
            Text.assemble(
                ("\n❌ 验证失败，请检查上面的错误信息\n", "bold red")
            ),
            title="验证失败",
            border_style="red"
        ))


async def main():
    """主验证函数"""
    console.print(Panel(
        Text("KamaClaude 验证工具", style="bold cyan"),
        border_style="cyan"
    ))
    
    checks = []
    checks.append(check_env())
    checks.append(check_imports())
    checks.append(await test_agent())
    checks.append(check_ui_files())
    
    all_ok = all(checks)
    print_summary(all_ok)
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n\n用户中断", style="yellow")
        sys.exit(1)
