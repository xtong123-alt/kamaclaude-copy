import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

from kamaclaude.core.llm import LLMProvider
from kamaclaude.core.tools import ToolRegistry
from kamaclaude.core.eventbus import EventBus
from kamaclaude.core.session import SessionManager
from kamaclaude.core.agent import Agent


console = Console()


# Big ASCII Logo
LOGO = """
██╗  ██╗ █████╗ ███╗   ███╗ █████╗  ██████╗██╗      █████╗ 
██║ ██╔╝██╔══██╗████╗ ████║██╔══██╗██╔════╝██║     ██╔══██╗
█████╔╝ ███████║██╔████╔██║███████║██║     ██║     ███████║
██╔═██╗ ██╔══██║██║╚██╔╝██║██╔══██║██║     ██║     ██╔══██║
██║  ██╗██║  ██║██║ ╚═╝ ██║██║  ██║╚██████╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝
"""


class SimpleKamaTUI:
    """简单但美观的 KamaClaude TUI"""
    
    def __init__(self):
        self.llm = None
        self.tools = None
        self.eventbus = None
        self.sessions = None
        self.agent = None
        self.session_id = None
        self.task_running = False
    
    def init(self):
        """初始化所有组件"""
        with console.status("[bold cyan]正在初始化 KamaClaude...[/]"):
            self.llm = LLMProvider()
            self.tools = ToolRegistry()
            self.eventbus = EventBus()
            self.sessions = SessionManager()
            self.agent = Agent(self.llm, self.tools, self.eventbus, self.sessions)
            
            # 自动允许所有权限
            for tool in self.tools.get_all_tools():
                self.tools.allow_always(tool.name)
            
            # 创建会话
            session = self.sessions.create_session()
            self.session_id = session.id
            
            # 订阅事件
            self.eventbus.subscribe_all(self._handle_event)
    
    def _handle_event(self, evt):
        """处理来自 Agent 的事件"""
        etype = evt.type.value
        data = evt.data
        
        try:
            if etype == "run_start":
                console.print(Text.assemble(("\n", ""), ("run ", "dim white"), (data.get("goal", "")[:60], "bold cyan")))
            
            elif etype == "step_start":
                console.print(Text.assemble(("step ", "dim white"), (str(data.get("index", 0)), "white")))
            
            elif etype == "thought":
                thought = data.get("thought", "")
                if thought:
                    console.print(Text.assemble(("  💭 ", "dim cyan"), (thought, "cyan")))
            
            elif etype == "tool_call":
                name = data.get("name", "")
                args = data.get("arguments", {})
                args_str = ", ".join(f"{k}={v}" for k, v in args.items())
                console.print(Text.assemble(
                    ("  🔧 ", "blue"),
                    ("tool ", "dim blue"),
                    (name, "bold blue"),
                    (f" {args_str}", "dim")
                ))
            
            elif etype == "tool_result":
                content = data.get("content", "")
                if data.get("is_error"):
                    console.print(Text.assemble(("    ✗ ", "red"), (content[:80], "red")))
                else:
                    console.print(Text.assemble(("    ✓ ", "green"), (content[:80], "dim")))
            
            elif etype == "context_watermark":
                ctx = data
                in_tok = ctx.get("in", 0)
                out_tok = ctx.get("out", 0)
                cache = ctx.get("cache", 0)
                watermark = ctx.get("watermark", 0) * 100
                
                # 进度条
                filled = int(watermark / 5)
                bar = "█" * filled + "░" * (20 - filled)
                
                console.print(Text.assemble(
                    ("  tokens", "dim"),
                    (f" in={in_tok} ", "dim green"),
                    (f"out={out_tok} ", "dim red"),
                    (f"cache={cache} ", "dim yellow"),
                    (f"ctx:{watermark:.1f}% ", "dim cyan"),
                    (f"[{bar}]", "cyan" if watermark < 70 else "yellow")
                ))
            
            elif etype == "run_complete":
                status = data.get("status", "")
                if status == "completed":
                    console.print(Text.assemble(("✓ ", "bold green"), ("completed", "bold green")))
                else:
                    error = data.get("error", "")
                    console.print(Text.assemble(("✗ ", "bold red"), ("failed: ", "bold red"), (error, "red")))
            
            elif etype == "error":
                console.print(Text.assemble(("✗ ", "bold red"), (data.get("error", ""), "red")))
        
        except Exception as e:
            # 防止事件处理导致崩溃
            pass
    
    async def run_task(self, goal: str):
        """运行一个任务"""
        self.task_running = True
        try:
            await self.agent.run(self.session_id, goal)
        except Exception as e:
            console.print(Text(f"错误: {e}", style="bold red"))
        finally:
            self.task_running = False
    
    def print_header(self):
        """打印顶部栏"""
        # 清空屏幕（简单方式）
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # 打印 Logo
        console.print(Panel(Text(LOGO, style="#00d4ff"), border_style="#00d4ff"))
        
        # 打印状态栏
        session_short = self.session_id[:12] if self.session_id else "sess-xxxxxx"
        status_line = Text.assemble(
            ("KamaClaude", "bold #00d4ff"),
            ("  127.0.0.1:7437", "#666"),
            (f"  sess-{session_short}", "#666"),
            ("  [ready]", "#00ff88")
        )
        console.print(status_line)
        console.print()
        
        # 打印提示
        console.print(Text("输入消息开始对话 · 键入 / 触发 skill · Ctrl+C 退出", style="dim"))
        console.print()
    
    def show_skills(self):
        """显示可用的 skills"""
        console.print(Panel(
            Text.assemble(
                ("/compact", "bold cyan"), (" - 压缩上下文窗口\n", "dim"),
                ("/init", "bold cyan"), (" - 分析当前项目\n", "dim"),
                ("/summarize", "bold cyan"), (" - 总结会话", "dim"),
            ),
            title="Skills",
            border_style="cyan"
        ))
    
    async def run(self):
        """主运行循环"""
        self.init()
        self.print_header()
        
        console.print(Text("欢迎使用 KamaClaude！输入任务开始...", style="dim cyan"))
        console.print()
        
        try:
            while True:
                try:
                    if self.task_running:
                        # 正在运行任务，不接受输入
                        await asyncio.sleep(0.1)
                        continue
                    
                    # 获取用户输入
                    user_input = Prompt.ask("[bold green]> [/]")
                    
                    if user_input is None or user_input.lower() in ["quit", "exit", "q"]:
                        console.print("\n再见！👋", style="cyan")
                        break
                    
                    if not user_input.strip():
                        continue
                    
                    # 处理 skill
                    if user_input == "/" or user_input.startswith("/"):
                        if user_input == "/":
                            self.show_skills()
                        else:
                            console.print(Text(f"执行 skill: {user_input}", style="cyan"))
                        continue
                    
                    # 执行任务
                    console.print()
                    await self.run_task(user_input)
                    console.print()
                
                except KeyboardInterrupt:
                    console.print("\n\n再见！👋", style="cyan")
                    break
                except Exception as e:
                    console.print(f"\n错误: {e}", style="red")
        
        except KeyboardInterrupt:
            console.print("\n\n再见！👋", style="cyan")


async def main():
    """主函数"""
    app = SimpleKamaTUI()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
