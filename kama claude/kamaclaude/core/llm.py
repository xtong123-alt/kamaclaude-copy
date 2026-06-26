import os
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv
from .types import Message, ToolCall, ContextStats

load_dotenv()


class LLMProvider:
    def __init__(self):
        # 优先使用阿里云百炼，其次是 DeepSeek，最后是 OpenAI
        self.api_key = os.getenv('ALIYUN_API_KEY', os.getenv('DEEPSEEK_API_KEY', os.getenv('OPENAI_API_KEY', '')))
        self.base_url = os.getenv('ALIYUN_BASE_URL', os.getenv('DEEPSEEK_BASE_URL', os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')))
        self.model = os.getenv('ALIYUN_MODEL', os.getenv('DEEPSEEK_MODEL', os.getenv('OPENAI_MODEL', 'qwen-plus')))
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        self.stats = ContextStats()
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
    ) -> tuple[Message, ContextStats]:
        formatted_messages = []
        
        if system_prompt:
            formatted_messages.append({'role': 'system', 'content': system_prompt})
        
        for msg in messages:
            formatted_msg = {'role': msg.role, 'content': msg.content}
            if msg.tool_calls:
                formatted_msg['tool_calls'] = [
                    {
                        'id': tc.id,
                        'type': 'function',
                        'function': {'name': tc.name, 'arguments': str(tc.arguments)},
                    }
                    for tc in msg.tool_calls
                ]
            formatted_messages.append(formatted_msg)
        
        kwargs = {
            'model': self.model,
            'messages': formatted_messages,
        }
        
        if tools:
            kwargs['tools'] = tools
        
        response = await self.client.chat.completions.create(**kwargs)
        
        choice = response.choices[0]
        message = choice.message
        
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=eval(tc.function.arguments),
                    )
                )
        
        result_msg = Message(
            role=message.role,
            content=message.content or '',
            tool_calls=tool_calls if tool_calls else None,
        )
        
        self.stats.input_tokens += response.usage.prompt_tokens
        self.stats.output_tokens += response.usage.completion_tokens
        self.stats.total_tokens += response.usage.total_tokens
        
        return result_msg, self.stats.model_copy()
