from dataclasses import dataclass
import json
from typing import Any

import httpx
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

from client.tools import AVAILABLE_TOOLS, TOOLS

URL = "http://localhost:8000"


@dataclass
class StreamResult:
    tool_calls_detected: bool
    content: str
    tool_calls: list[ChatCompletionMessageToolCallParam]


def _make_empty_tool_call() -> ChatCompletionMessageToolCallParam:
    return {
        "id": "",
        "type": "function",
        "function": {"name": "", "arguments": ""},
    }


def _accumulate_tool_call(
    tool_calls: list[ChatCompletionMessageToolCallParam],
    tc_data: dict[str, Any],
) -> None:
    index = tc_data["index"]
    function_info = tc_data.get("function", {})

    while len(tool_calls) <= index:
        tool_calls.append(_make_empty_tool_call())

    current = tool_calls[index]
    if tc_data.get("id"):
        current["id"] = tc_data["id"]
    if function_info.get("name"):
        current["function"]["name"] += function_info["name"]
    if function_info.get("arguments"):
        current["function"]["arguments"] += function_info["arguments"]


def _display_event(event: dict[str, Any], state: dict[str, bool]) -> str | None:
    event_type = event["type"]

    if event_type == "reasoning":
        if not state.get("reasoning_active"):
            print("[THINKING] ", end="", flush=True)
            state["reasoning_active"] = True
        print(event["data"], end="", flush=True)
        return None

    if event_type == "content":
        if not state.get("output_started"):
            if state.get("reasoning_active"):
                print("\n\n[OUTPUT]\n", flush=True)
            else:
                print("[OUTPUT] ", end="", flush=True)
            state["output_started"] = True
        print(event["data"], end="", flush=True)
        return event["data"]

    return None


def _parse_stream(response: httpx.Response) -> StreamResult:
    buffer = ""
    tool_calls: list[ChatCompletionMessageToolCallParam] = []
    content_parts: list[str] = []
    tool_calls_detected = False
    state: dict[str, bool] = {"reasoning_active": False, "output_started": False}

    for chunk in response.iter_text():
        buffer += chunk
        while "\n\n" in buffer:
            line, buffer = buffer.split("\n\n", 1)
            if not line.startswith("data: "):
                continue

            data = line[6:]
            if data == "[DONE]":
                break

            event = json.loads(data)

            if event["type"] == "tool_call":
                tool_calls_detected = True
                _accumulate_tool_call(tool_calls, event["data"])
            else:
                content = _display_event(event, state)
                if content is not None:
                    content_parts.append(content)

    if state.get("reasoning_active"):
        print()

    return StreamResult(
        tool_calls_detected=tool_calls_detected,
        content="".join(content_parts),
        tool_calls=tool_calls,
    )


def _execute_single_tool_call(
    tc: ChatCompletionMessageToolCallParam,
) -> ChatCompletionToolMessageParam:
    func_name = tc["function"]["name"]
    args = json.loads(tc["function"]["arguments"])
    print(f"  Calling {func_name}({args})")

    if func_name in AVAILABLE_TOOLS:
        result = AVAILABLE_TOOLS[func_name](**args)
        print(f"  Result: {result}")
        return ChatCompletionToolMessageParam(
            role="tool",
            tool_call_id=tc["id"],
            content=str(result),
        )

    return ChatCompletionToolMessageParam(
        role="tool",
        tool_call_id=tc["id"],
        content=f"Error: Tool '{func_name}' not found",
    )


def _execute_tools(
    tool_calls: list[ChatCompletionMessageToolCallParam],
) -> list[ChatCompletionToolMessageParam]:
    print("\n[TOOL CALLS]")
    results = [_execute_single_tool_call(tc) for tc in tool_calls]
    print()
    return results


def _build_payload(
    messages: list[ChatCompletionMessageParam], session_id: str | None
) -> dict[str, Any]:
    return {
        "messages": messages,
        "session_id": session_id,
        "enable_reasoning": True,
        "tools": TOOLS,
    }


def _handle_response(result: StreamResult) -> bool:
    if result.content:
        return False

    if result.tool_calls_detected:
        return True

    return False


def run_conversation(
    prompt: str, session_id: str | None = None
) -> tuple[str | None, list[ChatCompletionMessageParam]]:
    messages: list[ChatCompletionMessageParam] = [
        ChatCompletionUserMessageParam(role="user", content=prompt)
    ]

    while True:
        payload = _build_payload(messages, session_id)

        with httpx.Client() as client:
            with client.stream(
                "POST", f"{URL}/chat", json=payload, timeout=120.0
            ) as response:
                response.raise_for_status()
                result = _parse_stream(response)

        if result.tool_calls_detected:
            messages.append(
                {
                    "role": "assistant",
                    "content": result.content if result.content else None,
                    "tool_calls": result.tool_calls,
                }
            )
            tool_results = _execute_tools(result.tool_calls)
            messages.extend(tool_results)
        else:
            break

    return session_id, messages


def list_sessions() -> list[dict[str, Any]]:
    with httpx.Client() as client:
        response = client.get(f"{URL}/sessions")
        response.raise_for_status()
        return response.json()


def delete_session(session_id: str) -> bool:
    with httpx.Client() as client:
        response = client.delete(f"{URL}/sessions/{session_id}")
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True
