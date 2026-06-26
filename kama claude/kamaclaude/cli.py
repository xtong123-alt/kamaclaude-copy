import asyncio
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from .core.ipc import IPCClient

app = typer.Typer()
console = Console()


async def _connect():
    client = IPCClient()
    await client.connect()
    return client


@app.command()
def start():
    """启动 kama-core 守护进程"""
    from .core.daemon import main
    asyncio.run(main())


@app.command()
def chat(message: Optional[str] = typer.Argument(None)):
    """与 KamaClaude 对话"""
    
    async def _chat():
        client = await _connect()
        
        resp = await client.request("create_session")
        session_id = resp.data["session_id"]
        
        console.print(f"[bold cyan]Session: {session_id}[/bold cyan]")
        
        if message:
            await _send_message(client, session_id, message)
        
        console.print("\n[dim]输入消息继续对话，输入 'quit' 退出[/dim]")
        
        try:
            while True:
                msg = console.input("\n[bold green]> [/bold green]")
                if msg.lower() in ["quit", "exit", "q"]:
                    break
                if msg.strip():
                    await _send_message(client, session_id, msg)
        except KeyboardInterrupt:
            pass
    
    asyncio.run(_chat())


async def _send_message(client: IPCClient, session_id: str, message: str):
    async def on_event(msg):
        if msg.type == "event":
            evt = msg.data
            _print_event(evt)
    
    client.on_event(on_event)
    
    await client.request("run", {"session_id": session_id, "goal": message})
    
    await asyncio.sleep(0.5)


def _print_event(evt):
    etype = evt["type"]
    data = evt["data"]
    
    if etype == "thought":
        console.print(f"[dim]💭[/dim] {data['thought']}")
    elif etype == "tool_call":
        console.print(f"[blue]🔧 {data['name']}[/blue] {data['arguments']}")
    elif etype == "tool_result":
        if data["is_error"]:
            console.print(f"[red]✗[/red] {data['content'][:200]}...")
        else:
            console.print(f"[green]✓[/green] {data['content'][:200]}...")
    elif etype == "permission_request":
        console.print(Panel(
            Text(f"⚠️  需要权限: {data['tool_name']}", style="yellow"),
            title="权限请求",
        ))
    elif etype == "run_complete":
        status = data.get("status")
        if status == "completed":
            console.print("\n[bold green]✓ 完成[/bold green]")
        else:
            console.print(f"\n[bold red]✗ 失败: {data.get('error')}[/bold red]")


if __name__ == "__main__":
    app()
