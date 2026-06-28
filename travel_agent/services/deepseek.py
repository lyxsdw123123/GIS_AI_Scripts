"""DeepSeek API 调用（兼容 OpenAI SDK）"""
from __future__ import annotations

from openai import AsyncOpenAI

from travel_agent.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    timeout=30.0,  # 单次 LLM 调用最长等 30 秒
)


async def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict:
    """
    调用 DeepSeek，返回 OpenAI 格式的 message dict。
    支持 function calling 的完整循环：如果模型返回 tool_calls，
    调用方需要执行工具，然后把结果追加到 messages 再次调用。
    """
    kwargs = dict(
        model=DEEPSEEK_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    resp = await client.chat.completions.create(**kwargs)
    choice = resp.choices[0]
    msg = choice.message

    result = {
        "role": "assistant",
        "content": msg.content or "",
    }
    if msg.tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    return result
