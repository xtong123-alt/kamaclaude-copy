import os
import subprocess
from typing import Dict, Any, List, Callable, Optional
from pathlib import Path
from .types import ToolCall, ToolResult


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
        requires_permission: bool = True,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.requires_permission = requires_permission
    
    def to_openai_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.permission_rules: Dict[str, bool] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        self.register_tool(
            Tool(
                name="list_dir",
                description="列出目录内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "目录路径"},
                        "max_depth": {"type": "integer", "description": "最大深度", "default": 2},
                    },
                    "required": ["path"],
                },
                handler=self._list_dir,
                requires_permission=False,
            )
        )
        
        self.register_tool(
            Tool(
                name="read_file",
                description="读取文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "文件路径"},
                    },
                    "required": ["path"],
                },
                handler=self._read_file,
                requires_permission=False,
            )
        )
        
        self.register_tool(
            Tool(
                name="write_file",
                description="写入文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "文件路径"},
                        "content": {"type": "string", "description": "文件内容"},
                    },
                    "required": ["path", "content"],
                },
                handler=self._write_file,
                requires_permission=True,
            )
        )
        
        self.register_tool(
            Tool(
                name="bash",
                description="执行 bash 命令",
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "要执行的命令"},
                    },
                    "required": ["command"],
                },
                handler=self._bash,
                requires_permission=True,
            )
        )
    
    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[Tool]:
        return list(self.tools.values())
    
    def get_openai_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_openai_schema() for tool in self.tools.values()]
    
    def needs_permission(self, tool_name: str) -> bool:
        if tool_name in self.permission_rules:
            return not self.permission_rules[tool_name]
        tool = self.get_tool(tool_name)
        return tool.requires_permission if tool else True
    
    def allow_always(self, tool_name: str):
        self.permission_rules[tool_name] = True
    
    def deny_always(self, tool_name: str):
        self.permission_rules[tool_name] = False
    
    async def execute(self, tool_call: ToolCall) -> ToolResult:
        tool = self.get_tool(tool_call.name)
        if not tool:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Unknown tool: {tool_call.name}",
                is_error=True,
            )
        
        try:
            result = await tool.handler(**tool_call.arguments)
            return ToolResult(
                tool_call_id=tool_call.id,
                content=str(result),
                is_error=False,
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Error executing {tool_call.name}: {str(e)}",
                is_error=True,
            )
    
    async def _list_dir(self, path: str, max_depth: int = 2) -> str:
        def _list_recursive(p: Path, depth: int) -> str:
            if depth > max_depth:
                return ""
            result = []
            try:
                for item in p.iterdir():
                    prefix = "  " * depth
                    if item.is_dir():
                        result.append(f"{prefix}{item.name}/")
                        result.append(_list_recursive(item, depth + 1))
                    else:
                        result.append(f"{prefix}{item.name}")
            except PermissionError:
                result.append(f"{prefix}[permission denied]")
            return "\n".join(result)
        
        return _list_recursive(Path(path), 0)
    
    async def _read_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    async def _write_file(self, path: str, content: str) -> str:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written: {path}"
    
    async def _bash(self, command: str) -> str:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        if result.returncode != 0:
            output += f"\nExit code: {result.returncode}"
        return output
