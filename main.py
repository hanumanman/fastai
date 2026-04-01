import json
from typing import Any, AsyncGenerator, cast

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from tools.models import ToolDefinition
from tools.streaming import handle_finish_reason, handle_tool_calls

app = FastAPI()


class Settings(BaseSettings):
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = ""
    model: str = "qwen/qwen3.6-plus-preview:free"
    model_config = {"env_file": ".env"}


settings = Settings()

openrouter_client = AsyncOpenAI(
    base_url=settings.base_url,
    api_key=settings.api_key,
)


class ChatMessage(BaseModel):
    role: str
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    enable_reasoning: bool = True
    tools: list[ToolDefinition] | None = None
    tool_choice: str | dict[str, Any] | None = None
    parallel_tool_calls: bool | None = None


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.post("/chat")
async def chat(request: ChatRequest):
    messages: list[ChatCompletionMessageParam] = cast(
        list[ChatCompletionMessageParam],
        [m.model_dump(exclude_none=True) for m in request.messages],
    )

    response = await openrouter_client.chat.completions.create(
        model=settings.model,
        messages=messages,
        stream=True,
        tools=cast(
            Any, [t.model_dump() for t in request.tools] if request.tools else None
        ),
        tool_choice=cast(Any, request.tool_choice),
        parallel_tool_calls=cast(Any, request.parallel_tool_calls),
        extra_body={"reasoning": {"enabled": request.enable_reasoning}},
    )

    return StreamingResponse(
        _stream_chunks(response, request.enable_reasoning),
        media_type="text/event-stream",
    )


async def _stream_chunks(
    stream: AsyncStream[ChatCompletionChunk], enable_reasoning: bool
) -> AsyncGenerator[str, None]:
    async for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        finish_reason = chunk.choices[0].finish_reason

        if enable_reasoning:
            reasoning = getattr(delta, "reasoning", None)
            if reasoning:
                yield f"data: {json.dumps({'type': 'reasoning', 'data': reasoning})}\n\n"

        for event in handle_tool_calls(delta):
            yield event

        for event in handle_finish_reason(finish_reason):
            yield event

        content = delta.content
        if content:
            yield f"data: {json.dumps({'type': 'content', 'data': content})}\n\n"

    yield "data: [DONE]\n\n"
