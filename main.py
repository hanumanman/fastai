import json
from typing import Any, AsyncGenerator, cast

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import (
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolUnionParam,
)
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from sessions import SessionInfo, SessionStore, store
from tools.streaming import handle_finish_reason, handle_tool_calls

app = FastAPI()


class Settings(BaseSettings):
    base_url: str
    api_key: str
    model: str
    model_config = {"env_file": ".env"}


settings = Settings()  # type: ignore[call-arg]  # ty:ignore[missing-argument]

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
    session_id: str | None = None
    enable_reasoning: bool = True
    tools: list[ChatCompletionToolUnionParam]
    tool_choice: ChatCompletionToolChoiceOptionParam
    parallel_tool_calls: bool


class ChatResponse(BaseModel):
    session_id: str


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.get("/sessions")
async def list_sessions() -> list[SessionInfo]:
    sessions = store.list_all()
    return [SessionInfo(id=s.id, message_count=len(s.messages)) for s in sessions]


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict[str, str]:
    if not store.delete(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}


@app.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    session_id = request.session_id
    if not session_id:
        stored_messages: list[ChatCompletionMessageParam] = []
    else:
        session = store.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        stored_messages = session.messages

    incoming: list[ChatCompletionMessageParam] = [
        m.model_dump(exclude_none=True) for m in request.messages
    ]
    all_messages: list[ChatCompletionMessageParam] = stored_messages + incoming

    if not session_id:
        session_id = store.create(all_messages).id
    else:
        store.update(session_id, all_messages)

    response = await openrouter_client.chat.completions.create(
        model=settings.model,
        messages=all_messages,
        stream=True,
        tools=request.tools,
        tool_choice=request.tool_choice,
        parallel_tool_calls=request.parallel_tool_calls,
        extra_body={"reasoning": {"enabled": request.enable_reasoning}},
    )

    return StreamingResponse(
        _stream_chunks(response, request.enable_reasoning, session_id, all_messages),
        media_type="text/event-stream",
    )


async def _stream_chunks(
    stream: AsyncStream[ChatCompletionChunk],
    enable_reasoning: bool,
    session_id: str,
    messages: list[ChatCompletionMessageParam],
    store_instance: SessionStore = store,
) -> AsyncGenerator[str, None]:
    content_parts: list[str] = []
    tool_calls_accum: dict[int, dict[str, Any]] = {}
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
            evt = json.loads(event[6:])
            tc = evt["data"]
            idx = tc["index"]
            if idx not in tool_calls_accum:
                tool_calls_accum[idx] = {
                    "id": "",
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                }
            if tc.get("id"):
                tool_calls_accum[idx]["id"] = tc["id"]
            fn = tc.get("function", {})
            if fn.get("name"):
                tool_calls_accum[idx]["function"]["name"] += fn["name"]
            if fn.get("arguments"):
                tool_calls_accum[idx]["function"]["arguments"] += fn["arguments"]

        for event in handle_finish_reason(finish_reason):
            yield event

        content = delta.content
        if content:
            content_parts.append(content)
            yield f"data: {json.dumps({'type': 'content', 'data': content})}\n\n"

    assistant_msg: dict[str, Any] = {"role": "assistant"}
    if content_parts:
        assistant_msg["content"] = "".join(content_parts)
    if tool_calls_accum:
        assistant_msg["tool_calls"] = list(tool_calls_accum.values())
    messages.append(cast(ChatCompletionMessageParam, assistant_msg))
    store_instance.update(session_id, messages)

    yield "data: [DONE]\n\n"
