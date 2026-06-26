import asyncio
import uuid
from typing import Optional, List
from datetime import datetime
from .types import (
    Message,
    Event,
    EventType,
    Run,
    RunStatus,
    Step,
    ToolCall,
    ToolResult,
    PermissionDecision,
    ContextStats,
)
from .llm import LLMProvider
from .tools import ToolRegistry
from .eventbus import EventBus
from .session import SessionManager


SYSTEM_PROMPT = """你是 KamaClaude，一个智能编程助手。你的任务是帮助用户完成编程相关的任务。

你可以使用工具来：
1. 查看和操作文件系统
2. 执行命令
3. 编写代码

工作流程：
1. 理解用户的目标
2. 思考下一步该做什么
3. 调用合适的工具
4. 根据工具结果继续，直到任务完成

重要规则：
- 每次只执行一个明确的步骤
- 清晰地表达你的思考过程
- 如果任务复杂，可以分多个步骤完成
- 完成后总结结果
"""


class Agent:
    def __init__(
        self,
        llm: LLMProvider,
        tools: ToolRegistry,
        eventbus: EventBus,
        sessions: SessionManager,
    ):
        self.llm = llm
        self.tools = tools
        self.eventbus = eventbus
        self.sessions = sessions
        self._pending_permission: Optional[dict] = None
    
    async def run(
        self,
        session_id: str,
        goal: str,
    ) -> Run:
        run_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        run = Run(
            id=run_id,
            session_id=session_id,
            goal=goal,
            status=RunStatus.RUNNING,
        )
        
        await self._emit_event(
            EventType.RUN_START,
            {"goal": goal},
            session_id=session_id,
            run_id=run_id,
        )
        
        session = self.sessions.get_session(session_id)
        if not session:
            run.status = RunStatus.FAILED
            run.error = "Session not found"
            return run
        
        try:
            user_msg = Message(role="user", content=goal)
            self.sessions.add_message(session_id, user_msg)
            
            step_index = 0
            while run.status == RunStatus.RUNNING:
                step = await self._step(run, session, step_index)
                run.steps.append(step)
                
                if step.status == RunStatus.COMPLETED:
                    if not step.tool_calls:
                        run.status = RunStatus.COMPLETED
                        break
                
                step_index += 1
                
                if step_index > 50:
                    run.status = RunStatus.FAILED
                    run.error = "Max steps exceeded"
                    break
            
        except Exception as e:
            run.status = RunStatus.FAILED
            run.error = str(e)
            await self._emit_event(
                EventType.ERROR,
                {"error": str(e)},
                session_id=session_id,
                run_id=run_id,
            )
        
        run.completed_at = datetime.now()
        await self._emit_event(
            EventType.RUN_COMPLETE,
            {"status": run.status, "error": run.error},
            session_id=session_id,
            run_id=run_id,
        )
        
        self.sessions.save_run(run)
        return run
    
    async def _step(self, run: Run, session: Session, step_index: int) -> Step:
        step_id = f"step-{uuid.uuid4().hex[:8]}"
        step = Step(
            id=step_id,
            run_id=run.id,
            index=step_index,
            status=RunStatus.RUNNING,
        )
        
        await self._emit_event(
            EventType.STEP_START,
            {"index": step_index},
            session_id=session.id,
            run_id=run.id,
            step_id=step_id,
        )
        
        messages = session.thread.copy()
        
        response, stats = await self.llm.chat(
            messages=messages,
            tools=self.tools.get_openai_schemas(),
            system_prompt=SYSTEM_PROMPT,
        )
        
        step.thought = response.content
        
        if response.content:
            await self._emit_event(
                EventType.THOUGHT,
                {"thought": response.content},
                session_id=session.id,
                run_id=run.id,
                step_id=step_id,
            )
        
        # 发送 token 统计信息
        ctx_data = {
            "in": stats.input_tokens,
            "out": stats.output_tokens,
            "cache": stats.cache_tokens,
            "watermark": stats.watermark,
        }
        await self._emit_event(
            EventType.CONTEXT_WATERMARK,
            ctx_data,
            session_id=session.id,
            run_id=run.id,
            step_id=step_id,
        )
        
        if response.tool_calls:
            step.tool_calls = response.tool_calls
            
            for tool_call in response.tool_calls:
                await self._emit_event(
                    EventType.TOOL_CALL,
                    {"name": tool_call.name, "arguments": tool_call.arguments},
                    session_id=session.id,
                    run_id=run.id,
                    step_id=step_id,
                )
                
                if self.tools.needs_permission(tool_call.name):
                    decision = await self._request_permission(tool_call, run, session, step)
                    if decision in [PermissionDecision.DENY_ONCE, PermissionDecision.DENY_ALWAYS]:
                        result = ToolResult(
                            tool_call_id=tool_call.id,
                            content="Permission denied",
                            is_error=True,
                        )
                        step.tool_results.append(result)
                        continue
                    if decision == PermissionDecision.ALLOW_ALWAYS:
                        self.tools.allow_always(tool_call.name)
                
                result = await self.tools.execute(tool_call)
                step.tool_results.append(result)
                
                await self._emit_event(
                    EventType.TOOL_RESULT,
                    {
                        "tool_call_id": result.tool_call_id,
                        "content": result.content,
                        "is_error": result.is_error,
                    },
                    session_id=session.id,
                    run_id=run.id,
                    step_id=step_id,
                )
            
            assistant_msg = Message(
                role="assistant",
                content=response.content or "",
                tool_calls=response.tool_calls,
            )
            self.sessions.add_message(session.id, assistant_msg)
            
            for result in step.tool_results:
                tool_msg = Message(
                    role="tool",
                    content=result.content,
                )
                self.sessions.add_message(session.id, tool_msg)
        
        step.status = RunStatus.COMPLETED
        step.completed_at = datetime.now()
        
        await self._emit_event(
            EventType.STEP_COMPLETE,
            {},
            session_id=session.id,
            run_id=run.id,
            step_id=step_id,
        )
        
        return step
    
    async def _request_permission(
        self,
        tool_call: ToolCall,
        run: Run,
        session: Session,
        step: Step,
    ) -> PermissionDecision:
        permission_id = f"perm-{uuid.uuid4().hex[:8]}"
        
        await self._emit_event(
            EventType.PERMISSION_REQUEST,
            {
                "permission_id": permission_id,
                "tool_name": tool_call.name,
                "arguments": tool_call.arguments,
            },
            session_id=session.id,
            run_id=run.id,
            step_id=step.id,
        )
        
        self._pending_permission = {
            "id": permission_id,
            "event": asyncio.Event(),
            "decision": None,
        }
        
        run.status = RunStatus.WAITING_PERMISSION
        await self._pending_permission["event"].wait()
        run.status = RunStatus.RUNNING
        
        decision = self._pending_permission["decision"]
        self._pending_permission = None
        
        await self._emit_event(
            EventType.PERMISSION_RESPONSE,
            {"decision": decision},
            session_id=session.id,
            run_id=run.id,
            step_id=step.id,
        )
        
        return decision
    
    def respond_permission(self, decision: PermissionDecision):
        if self._pending_permission:
            self._pending_permission["decision"] = decision
            self._pending_permission["event"].set()
    
    async def _emit_event(
        self,
        event_type: EventType,
        data: dict,
        session_id: str = None,
        run_id: str = None,
        step_id: str = None,
    ):
        event = Event(
            id=f"evt-{uuid.uuid4().hex[:8]}",
            type=event_type,
            data=data,
            session_id=session_id,
            run_id=run_id,
            step_id=step_id,
        )
        await self.eventbus.emit(event)
