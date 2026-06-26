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

from textual.app import App, ComposeResult
from textual.widgets import (
    Static,
    Input,
    RichLog,
    Button,
    Label,
)
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from rich.text import Text
from rich.style import Style

from kamaclaude.core.llm import LLMProvider
from kamaclaude.core.tools import ToolRegistry
from kamaclaude.core.eventbus import EventBus
from kamaclaude.core.session import SessionManager
from kamaclaude.core.agent import Agent


# ASCII Art Logo - Big and Beautiful
KAMA_LOGO = """
██╗  ██╗ █████╗ ███╗   ███╗ █████╗  ██████╗██╗      █████╗ 
██║ ██╔╝██╔══██╗████╗ ████║██╔══██╗██╔════╝██║     ██╔══██╗
█████╔╝ ███████║██╔████╔██║███████║██║     ██║     ███████║
██╔═██╗ ██╔══██║██║╚██╔╝██║██╔══██║██║     ██║     ██╔══██║
██║  ██╗██║  ██║██║ ╚═╝ ██║██║  ██║╚██████╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝
"""


class KamaClaudeTUI(App):
    """美化后的 KamaClaude TUI 界面"""
    
    CSS = """
    * {
        box-sizing: border-box;
    }
    
    #app-container {
        height: 100%;
        layout: vertical;
        background: #0a0a0f;
    }
    
    /* 顶部状态栏 */
    #header-bar {
        height: 1;
        background: #1a1a2e;
        padding: 0 1;
        dock: top;
        layout: horizontal;
    }
    
    #header-bar Static {
        width: auto;
        height: 1;
    }
    
    #app-name {
        color: #00d4ff;
        font-weight: bold;
    }
    
    #server-info {
        color: #888;
    }
    
    #session-id {
        color: #888;
    }
    
    #status-indicator {
        margin-left: auto;
    }
    
    .status-ready {
        color: #00ff88;
    }
    
    .status-running {
        color: #ffcc00;
    }
    
    /* Logo 区域 */
    #logo-area {
        height: 8;
        background: #0f0f18;
        padding: 1;
        align: center middle;
    }
    
    #logo-area Static {
        color: #00d4ff;
    }
    
    #hint-text {
        width: 100%;
        text-align: center;
        color: #666;
        margin-top: 1;
    }
    
    /* 主内容区 */
    #content-area {
        height: 1fr;
        layout: vertical;
        padding: 1;
        overflow-y: auto;
        background: #0a0a0f;
    }
    
    /* 事件日志 */
    #event-log {
        height: 1fr;
        width: 100%;
        background: #0f0f18;
        border: solid #1a1a2e;
        padding: 1;
    }
    
    /* 输入区 */
    #input-area {
        height: 3;
        background: #12121a;
        padding: 0 1;
        dock: bottom;
        layout: horizontal;
        align: center middle;
        border-top: solid #2a2a3e;
    }
    
    #user-input {
        width: 1fr;
        height: 3;
        background: #1a1a2e;
        border: solid #2a2a3e;
        color: #fff;
        padding: 0 1;
    }
    
    #user-input:focus {
        border: solid #00d4ff;
    }
    
    /* 底部状态栏 */
    #footer-bar {
        height: 1;
        background: #12121a;
        padding: 0 1;
        dock: bottom;
        color: #666;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.llm = None
        self.tools = None
        self.eventbus = None
        self.sessions = None
        self.agent = None
        self.session_id = None
        self.task_is_running = False
        self.event_log_widget = None
    
    def compose(self) -> ComposeResult:
        with Container(id="app-container"):
            # 顶部状态栏
            with Container(id="header-bar"):
                yield Static("KamaClaude", id="app-name")
                yield Static("127.0.0.1:7437", id="server-info")
                yield Static("sess-000000000000", id="session-id")
                yield Static("ready", id="status-indicator", classes="status-ready")
            
            # Logo 区域
            with Container(id="logo-area"):
                yield Static(KAMA_LOGO)
                yield Static("输入消息开始对话 · 键入 / 触发 skill · Ctrl+C 退出", id="hint-text")
            
            # 主内容区
            with Container(id="content-area"):
                yield RichLog(id="event-log", markup=True, highlight=True, auto_scroll=True)
            
            # 输入区
            with Container(id="input-area"):
                yield Input(
                    placeholder="type a message - enter to send, ⌘/⌃+enter for newline",
                    id="user-input"
                )
            
            # 底部状态栏
            with Container(id="footer-bar"):
                yield Static("ready", id="footer-status")
    
    async def on_mount(self) -> None:
        """应用启动时初始化"""
        self.event_log_widget = self.query_one("#event-log", RichLog)
        
        # 初始化核心组件
        self.llm = LLMProvider()
        self.tools = ToolRegistry()
        self.eventbus = EventBus()
        self.sessions = SessionManager()
        self.agent = Agent(self.llm, self.tools, self.eventbus, self.sessions)
        
        # 自动允许所有权限（简化演示）
        for tool in self.tools.get_all_tools():
            self.tools.allow_always(tool.name)
        
        # 创建会话
        session = self.sessions.create_session()
        self.session_id = session.id
        
        # 更新界面
        self.query_one("#session-id", Static).update(f"sess-{session.id}")
        
        # 订阅事件
        self.eventbus.subscribe_all(self._on_event)
        
        # 欢迎信息
        self._write_welcome()
    
    def _write_welcome(self):
        """写入欢迎信息"""
        self.event_log_widget.write(Text("欢迎使用 KamaClaude！输入任务开始...", style="dim cyan"))
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """用户输入提交"""
        message = event.value.strip()
        if not message:
            return
        
        event.input.clear()
        
        # 检查是否正在运行
        if self.task_is_running:
            self.event_log_widget.write(Text("请等待当前任务完成...", style="yellow"))
            return
        
        # 处理 skill 触发
        if message == "/" or message.startswith("/"):
            self._handle_skill(message)
            return
        
        # 执行任务
        await self._run_task(message)
    
    def _handle_skill(self, message: str):
        """处理 skill 命令"""
        skills = {
            "/compact": "压缩上下文窗口",
            "/init": "分析当前项目",
            "/summarize": "总结会话",
        }
        
        if message == "/":
            # 显示所有可用 skills
            self.event_log_widget.write(Text("\n可用 Skills:", style="bold cyan"))
            for cmd, desc in skills.items():
                self.event_log_widget.write(Text(f"  [cyan]{cmd}[/cyan] - {desc}"))
        elif message in skills:
            self.event_log_widget.write(Text(f"执行 skill: {message}", style="cyan"))
            # 这里可以添加实际的 skill 执行逻辑
        else:
            self.event_log_widget.write(Text(f"未知 skill: {message}", style="red"))
    
    async def _run_task(self, goal: str):
        """运行任务"""
        self.task_is_running = True
        self._update_status("running")
        
        # 显示用户输入
        user_msg = Text.assemble(
            ("> ", "bold green"),
            (goal, "white")
        )
        self.event_log_widget.write(user_msg)
        
        try:
            await self.agent.run(self.session_id, goal)
        except Exception as e:
            self.event_log_widget.write(Text(f"错误: {e}", style="bold red"))
        finally:
            self.task_is_running = False
            self._update_status("ready")
    
    def _on_event(self, evt):
        """处理事件"""
        etype = evt.type.value
        data = evt.data
        
        # 在主线程更新 UI
        async def update_ui():
            if etype == "run_start":
                run_id = data.get("goal", "")[:50]
                self.event_log_widget.write(
                    Text.assemble(("\n", ""), ("run ", "dim white"), (run_id, "bold cyan"))
                )
            
            elif etype == "step_start":
                idx = data.get("index", 0)
                self.event_log_widget.write(
                    Text.assemble(("step ", "dim white"), (str(idx), "white"))
                )
            
            elif etype == "thought":
                thought = data.get("thought", "")
                self.event_log_widget.write(
                    Text.assemble(("  ", ""), ("💭 ", "dim cyan"), (thought, "cyan"))
                )
            
            elif etype == "tool_call":
                tool_name = data.get("name", "")
                args = data.get("arguments", {})
                args_str = ", ".join(f"{k}={v}" for k, v in args.items())
                self.event_log_widget.write(
                    Text.assemble(
                        ("  tool ", "dim blue"),
                        (tool_name, "bold blue"),
                        (f" {args_str}", "dim")
                    )
                )
            
            elif etype == "tool_result":
                content = data.get("content", "")[:100]
                if data.get("is_error"):
                    self.event_log_widget.write(
                        Text.assemble(("    ✗ ", "red"), (content, "red"))
                    )
                else:
                    self.event_log_widget.write(
                        Text.assemble(("    ✓ ", "green"), (content, "dim"))
                    )
            
            elif etype == "context_watermark":
                ctx = data
                in_tokens = ctx.get("in", 0)
                out_tokens = ctx.get("out", 0)
                cache = ctx.get("cache", 0)
                watermark = ctx.get("watermark", 0) * 100
                
                # 创建进度条
                filled = int(watermark / 5)
                bar = "█" * filled + "░" * (20 - filled)
                
                self.event_log_widget.write(
                    Text.assemble(
                        ("  tokens", "dim"),
                        (f" in={in_tokens} ", "dim green"),
                        (f"out={out_tokens} ", "dim red"),
                        (f"cache={cache} ", "dim yellow"),
                        (f"ctx:{watermark:.1f}% ", "dim cyan"),
                        (f"[{bar}]", "cyan" if watermark < 70 else "yellow")
                    )
                )
            
            elif etype == "run_complete":
                status = data.get("status", "")
                if status == "completed":
                    self.event_log_widget.write(
                        Text.assemble(("✓ ", "bold green"), ("completed", "bold green"))
                    )
                else:
                    error = data.get("error", "")
                    self.event_log_widget.write(
                        Text.assemble(("✗ ", "bold red"), ("failed: ", "bold red"), (error, "red"))
                    )
        
        # 调用 UI 更新
        asyncio.create_task(update_ui())
    
    def _update_status(self, status: str):
        """更新状态显示"""
        indicator = self.query_one("#status-indicator", Static)
        footer = self.query_one("#footer-status", Static)
        
        if status == "running":
            indicator.update("running")
            indicator.set_classes("status-running")
            footer.update("running")
        else:
            indicator.update("ready")
            indicator.set_classes("status-ready")
            footer.update("ready")


def main():
    """启动 KamaClaude TUI"""
    print("启动 KamaClaude...")
    app = KamaClaudeTUI()
    app.run()


if __name__ == "__main__":
    main()
