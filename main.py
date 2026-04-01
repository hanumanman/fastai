import json
from typing import AsyncGenerator, cast

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from pydantic import BaseModel
from pydantic_settings import BaseSettings

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
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    enable_reasoning: bool = True


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/chat")
async def chat(request: ChatRequest):
    messages: list[ChatCompletionMessageParam] = cast(
        list[ChatCompletionMessageParam],
        [{"role": m.role, "content": m.content} for m in request.messages],
    )

    response = await openrouter_client.chat.completions.create(
        model=settings.model,
        messages=messages,
        stream=True,
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
        delta = chunk.choices[0].delta if chunk.choices else None
        if not delta:
            continue

        if enable_reasoning:
            reasoning = getattr(delta, "reasoning", None)
            if reasoning:
                yield f"data: {json.dumps({'type': 'reasoning', 'data': reasoning})}\n\n"

        content = delta.content
        if content:
            yield f"data: {json.dumps({'type': 'content', 'data': content})}\n\n"

    yield "data: [DONE]\n\n"
