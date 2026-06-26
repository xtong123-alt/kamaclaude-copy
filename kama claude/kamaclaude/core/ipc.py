import asyncio
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel


class IPCMessage(BaseModel):
    type: str
    data: Dict[str, Any] = {}
    id: Optional[str] = None


class IPCClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 7437):
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._message_id = 0
        self._event_callbacks = []
    
    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        asyncio.create_task(self._listen())
    
    async def _listen(self):
        buffer = ""
        while True:
            try:
                data = await self.reader.read(4096)
                if not data:
                    break
                buffer += data.decode("utf-8")
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        await self._handle_message(line)
            except Exception as e:
                print(f"IPC listen error: {e}")
                break
    
    async def _handle_message(self, line: str):
        try:
            msg = IPCMessage(**json.loads(line))
            
            if msg.id and msg.id in self._pending_requests:
                fut = self._pending_requests.pop(msg.id)
                fut.set_result(msg)
            else:
                for callback in self._event_callbacks:
                    asyncio.create_task(callback(msg))
        except Exception as e:
            print(f"Error handling message: {e}")
    
    async def request(self, msg_type: str, data: Dict[str, Any] = None) -> IPCMessage:
        self._message_id += 1
        msg_id = str(self._message_id)
        msg = IPCMessage(type=msg_type, data=data or {}, id=msg_id)
        
        fut = asyncio.Future()
        self._pending_requests[msg_id] = fut
        
        await self._send(msg)
        return await fut
    
    async def send(self, msg_type: str, data: Dict[str, Any] = None):
        msg = IPCMessage(type=msg_type, data=data or {})
        await self._send(msg)
    
    async def _send(self, msg: IPCMessage):
        data = msg.model_dump_json() + "\n"
        self.writer.write(data.encode("utf-8"))
        await self.writer.drain()
    
    def on_event(self, callback):
        self._event_callbacks.append(callback)


class IPCServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 7437):
        self.host = host
        self.port = port
        self.clients = []
        self._handlers = {}
        self.server = None
    
    def register_handler(self, msg_type: str, handler):
        self._handlers[msg_type] = handler
    
    async def start(self):
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port,
        )
        print(f"IPC server listening on {self.host}:{self.port}")
    
    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        client = {"reader": reader, "writer": writer}
        self.clients.append(client)
        
        buffer = ""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                buffer += data.decode("utf-8")
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        await self._handle_client_message(client, line)
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            self.clients.remove(client)
            writer.close()
            await writer.wait_closed()
    
    async def _handle_client_message(self, client, line: str):
        try:
            msg = IPCMessage(**json.loads(line))
            
            if msg.type in self._handlers:
                response = await self._handlers[msg.type](msg.data)
                if msg.id:
                    await self._send_to_client(
                        client,
                        IPCMessage(type="response", data=response, id=msg.id),
                    )
        except Exception as e:
            print(f"Error handling client message: {e}")
    
    async def _send_to_client(self, client, msg: IPCMessage):
        data = msg.model_dump_json() + "\n"
        client["writer"].write(data.encode("utf-8"))
        await client["writer"].drain()
    
    async def broadcast(self, msg_type: str, data: Dict[str, Any] = None):
        msg = IPCMessage(type=msg_type, data=data or {})
        for client in self.clients[:]:
            try:
                await self._send_to_client(client, msg)
            except Exception as e:
                print(f"Broadcast error: {e}")
