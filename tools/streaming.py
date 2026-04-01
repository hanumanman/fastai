import json
from typing import Generator

from openai.types.chat.chat_completion_chunk import ChoiceDelta


def handle_tool_calls(delta: ChoiceDelta) -> Generator[str, None, None]:
    if delta.tool_calls:
        for tc in delta.tool_calls:
            yield f"data: {json.dumps({'type': 'tool_call', 'data': tc.model_dump()})}\n\n"


def handle_finish_reason(finish_reason: str | None) -> Generator[str, None, None]:
    if finish_reason == "tool_calls":
        yield f"data: {json.dumps({'type': 'finish', 'reason': 'tool_calls'})}\n\n"
    elif finish_reason == "stop":
        yield f"data: {json.dumps({'type': 'finish', 'reason': 'stop'})}\n\n"
