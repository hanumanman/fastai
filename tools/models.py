from typing import Any

from pydantic import BaseModel


class ToolFunction(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]
