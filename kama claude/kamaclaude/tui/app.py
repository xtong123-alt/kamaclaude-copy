import asyncio
from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    Static,
    Input,
    RichLog,
    Tree,
    Button,
    Label,
)
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from rich.text import Text
from rich.panel import Panel
from rich.style import Style
from ..core.ipc import IPCClient
from ..core.types import PermissionDecision


KAMA_LOGO = """
╔═══════════════════════════════════════════════════════════════╗
║  ██╗  ██╗ █████╗ ███╗   ███╗ █████╗  ██████╗██╗      █████╗  ║
║  ██║ ██╔╝██╔══██╗████╗ ████║██╔══██╗██╔════╝██║     ██╔══██╗ ║
║  █████╔╝ ███████║██╔████╔██║███████║██║     ██║     ███████║ ║
║  ██╔═██╗ ██╔══██║██║╚██╔╝██║██╔══██║██║     ██║     ██╔══██║ ║
║  ██║  ██╗██║  ██║██║ ╚═╝ ██║██║  ██║╚██████╗███████╗██║  ██║ ║
║  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ║
╚═══════════════════════════════════════════════════════════════╝
"""


class EventLog(RichLog):
    def __init__(self):
        super().__init__(markup=True, highlight=True, auto_scroll=True)
    
    def add_event(self, evt):
        etype = evt["type"]
        data = evt["data"]
        
        if etype == "run_start":
            self.write(Text.assemble(("[run] ", "bold blue"), data["goal"]))
        elif etype == "step_start":
            self.write(Text.assemble(("  step ", "dim"), str(data["index"])))
        elif etype == "thought":
            self.write(Text.assemble(("    💭 ", "dim cyan"), data["thought"]))
        elif etype == "tool_call":
            args = ", ".join(f"{k}={v}" for k, v in data["arguments"].items())
            self.write(Text.assemble(
                ("    🔧 ", "blue"),
                (data["name"], "bold blue"),
                (f" {args}", "dim"),
            ))
        elif etype == "tool_result":
            content = data["content"][:300]
            if data["is_error"]:
                self.write(Text.assemble(("      ✗ ", "red"), content))
            else:
                self.write(Text.assemble(("      ✓ ", "green"), content))
        elif etype == "permission_request":
            self.write(Text.assemble(
                ("    ⚠️  ", "bold yellow"),
                ("需要权限: ", "yellow"),
                (data["tool_name"], "bold yellow"),
            ))
        elif etype == "permission_response":
            self.write(Text.assemble(
                ("      ", "dim"),
                (data["decision"], "green" if "allow" in data["decision"] else "red"),
            ))
        elif etype == "context_watermark":
            ctx = data
            watermark_pct = int(ctx.get("watermark", 0) * 100)
            bar = "█" * (watermark_pct // 5) + "░" * (20 - watermark_pct // 5)
            self.write(Text.assemble(
                ("    ctx: ", "dim"),
                (f"[{bar}] {watermark_pct}%", "yellow" if watermark_pct > 70 else "dim"),
            ))
        elif etype == "run_complete":
            status = data.get("status")
            if status == "completed":
                self.write(Text.assemble(("[✓ completed] ", "bold green")))
            else:
                self.write(Text.assemble(("[✗ failed] ", "bold red"), data.get("error", "")))
        elif etype == "error":
            self.write(Text.assemble(("[!] ", "bold red"), data["error"]))


class PermissionDialog(Container):
    DEFAULT_CSS = """
    PermissionDialog {
        width: 60;
        height: 12;
        background: #2d2d2d;
        border: solid yellow;
        padding: 1;
        align: center middle;
    }
    
    PermissionDialog Label {
        width: 100%;
        text-align: center;
    }
    
    PermissionDialog Horizontal {
        height: 3;
        width: 100%;
        align: center middle;
    }
    
    PermissionDialog Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, tool_name: str, arguments: dict):
        super().__init__()
        self.tool_name = tool_name
        self.arguments = arguments
        self.callback = None
    
    def compose(self) -> ComposeResult:
        yield Label(f"⚠️  权限请求", classes="title")
        yield Label(f"工具: {self.tool_name}", id="perm-tool")
        yield Label(f"参数: {self.arguments}", id="perm-args")
        with Horizontal():
            yield Button("允许一次 (y)", id="allow-once", variant="success")
            yield Button("始终允许 (a)", id="allow-always", variant="success")
            yield Button("拒绝 (n)", id="deny-once", variant="error")
            yield Button("始终拒绝 (d)", id="deny-always", variant="error")
    
    def on_button_pressed(self, event: Button.Pressed):
        decision_map = {
            "allow-once": PermissionDecision.ALLOW_ONCE,
            "allow-always": PermissionDecision.ALLOW_ALWAYS,
            "deny-once": PermissionDecision.DENY_ONCE,
            "deny-always": PermissionDecision.DENY_ALWAYS,
        }
        if event.button.id in decision_map and self.callback:
            self.callback(decision_map[event.button.id])
        self.remove()


class SkillPalette(Container):
    DEFAULT_CSS = """
    SkillPalette {
        width: 40;
        height: 15;
        background: #1e1e1e;
        border: solid cyan;
        padding: 1;
        display: none;
    }
    
    SkillPalette.show {
        display: block;
    }
    
    SkillPalette Label {
        width: 100%;
        color: cyan;
        margin-bottom: 1;
    }
    
    SkillPalette .skill-item {
        padding: 0 1;
        height: 1;
    }
    
    SkillPalette .skill-item:hover {
        background: #2d2d2d;
    }
    """
    
    SKILLS = [
        ("/compact", "压缩上下文窗口"),
        ("/init", "分析当前项目，生成 .kama/context.md"),
        ("/orchestrate", "用 planner->executor->reviewer 多 Agent 工作流"),
        ("/review", "对指定路径做代码审查"),
        ("/summarize", "将当前 session 对话压缩为人类可读摘要"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Label("可用 Skills:")
        for cmd, desc in self.SKILLS:
            yield Label(f"  [cyan]{cmd}[/cyan]  {desc}", classes="skill-item")


class KamaTUI(App):
    CSS = """
    #main-container {
        height: 100%;
        layout: vertical;
    }
    
    #header {
        height: 3;
        background: #1a1a2e;
        padding: 0 1;
        align: left middle;
    }
    
    #content {
        height: 1fr;
        layout: horizontal;
    }
    
    #log-panel {
        width: 1fr;
        height: 100%;
        padding: 1;
    }
    
    #sidebar {
        width: 30;
        height: 100%;
        background: #16213e;
        padding: 1;
    }
    
    #input-container {
        height: 3;
        background: #0f0f23;
        padding: 0 1;
        align: center middle;
    }
    
    #input {
        width: 1fr;
    }
    
    #status {
        height: 1;
        background: #0f0f23;
        padding: 0 1;
        color: #888;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.session_id = None
        self.event_log = EventLog()
        self.show_skills = False
    
    def compose(self) -> ComposeResult:
        with Container(id="main-container"):
            with Container(id="header"):
                yield Static(KAMA_LOGO.strip(), id="logo")
                yield Static("127.0.0.1:7437", id="server-info")
                yield Static("ready", id="status-indicator")
            
            with Container(id="content"):
                with Container(id="log-panel"):
                    yield self.event_log
            
            with Container(id="input-container"):
                yield Input(placeholder="输入消息开始对话，键入 / 触发 skill", id="input")
            
            with Container(id="status"):
                yield Static("", id="status-text")
    
    async def on_mount(self) -> None:
        try:
            self.client = IPCClient()
            await self.client.connect()
            self.client.on_event(self._on_ipc_event)
            
            resp = await self.client.request("create_session")
            self.session_id = resp.data["session_id"]
            
            self.query_one("#status-indicator", Static).update("ready")
            self.query_one("#status-text", Static).update(f"Session: {self.session_id}")
            
            self.event_log.write(Text("输入消息开始对话...", style="dim"))
            
        except Exception as e:
            self.event_log.write(Text(f"无法连接到 kama-core: {e}", style="bold red"))
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        message = event.value.strip()
        if not message:
            return
        
        event.input.clear()
        
        if message == "/" or message.startswith("/"):
            if not self.show_skills:
                self.show_skills = True
                self.mount(SkillPalette())
                return
        
        if self.show_skills:
            self.show_skills = False
            for widget in self.query(SkillPalette):
                widget.remove()
        
        if self.client and self.session_id:
            self.query_one("#status-indicator", Static).update("running")
            await self.client.request("run", {"session_id": self.session_id, "goal": message})
    
    async def _on_ipc_event(self, msg):
        if msg.type == "event":
            evt = msg.data
            
            await self.run_async(lambda: self.event_log.add_event(evt))
            
            if evt["type"] == "permission_request":
                await self._show_permission_dialog(evt["data"])
            
            if evt["type"] == "run_complete":
                await self.run_async(lambda: self.query_one("#status-indicator", Static).update("ready"))
    
    async def _show_permission_dialog(self, data):
        dialog = PermissionDialog(data["tool_name"], data["arguments"])
        dialog.callback = self._on_permission_decision
        self.mount(dialog)
    
    def _on_permission_decision(self, decision: PermissionDecision):
        if self.client:
            asyncio.create_task(
                self.client.request("permission", {"decision": decision.value})
            )


def main():
    app = KamaTUI()
    app.run()


if __name__ == "__main__":
    main()
