from client.tools.docx_parser import parse_docx
from client.tools.find_file import find_file
from client.tools.pdf_parser import parse_pdf
from client.tools.weather import get_weather

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a given city",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "parse_pdf",
            "description": "Extract and return text content from a PDF file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the PDF file to parse",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum number of characters to return (default 10000)",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_file",
            "description": "Find files in the current codebase using fzf fuzzy matching",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to fuzzy match against file paths",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "parse_docx",
            "description": "Extract and return text content from a DOCX file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the DOCX file to parse",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum number of characters to return (default 10000)",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
]

AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "parse_pdf": parse_pdf,
    "find_file": find_file,
    "parse_docx": parse_docx,
}
