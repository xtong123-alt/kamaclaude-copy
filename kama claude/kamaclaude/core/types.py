from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class EventType(str, Enum):
    RUN_START = "run_start"
    RUN_COMPLETE = "run_complete"
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    THOUGHT = "thought"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    PERMISSION_REQUEST = "permission_request"
    PERMISSION_RESPONSE = "permission_response"
    CONTEXT_WATERMARK = "context_watermark"
    CONTEXT_COMPACT = "context_compact"
    ERROR = "error"
    LOG = "log"


class PermissionDecision(str, Enum):
    ALLOW_ONCE = "allow_once"
    ALLOW_ALWAYS = "allow_always"
    DENY_ONCE = "deny_once"
    DENY_ALWAYS = "deny_always"


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    tool_call_id: str
    content: str
    is_error: bool = False


class Message(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[ToolCall]] = None


class Event(BaseModel):
    id: str
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    run_id: Optional[str] = None
    step_id: Optional[str] = None


class Session(BaseModel):
    id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    thread: List[Message] = Field(default_factory=list)
    notes: Dict[str, str] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_PERMISSION = "waiting_permission"


class Run(BaseModel):
    id: str
    session_id: str
    goal: str
    status: RunStatus = RunStatus.PENDING
    steps: List["Step"] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class Step(BaseModel):
    id: str
    run_id: str
    index: int
    thought: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    status: RunStatus = RunStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class ContextStats(BaseModel):
    total_tokens: int = 0
    cache_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    watermark: float = 0.0
    is_compacted: bool = False
