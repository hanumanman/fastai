from typing import Any

import httpx
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)

from client import list_sessions, delete_session
from client.main import URL, _build_payload, _execute_tools, _parse_stream


COMMANDS: dict[str, str] = {
    "/new": "Start a new session",
    "/list": "List all sessions",
    "/switch <id>": "Switch to an existing session",
    "/delete <id>": "Delete a session",
    "/info": "Show current session info",
    "/help": "Show this help message",
    "/quit": "Exit the client",
}


def _print_sessions(sessions: list[dict[str, Any]]) -> None:
    if not sessions:
        print("No sessions found.")
        return
    print(f"\n{'ID':<14} {'Messages':<10}")
    print("-" * 24)
    for s in sessions:
        print(f"{s['id']:<14} {s['message_count']:<10}")
    print()


def _send_turn(
    messages: list[ChatCompletionMessageParam], session_id: str | None
) -> None:
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
        _send_turn(messages, session_id)


def main() -> None:
    session_id: str | None = None
    messages: list[ChatCompletionMessageParam] = []
    print("FastAI Chat Client (type /help for commands, /quit to leave)\n")

    while True:
        prefix = f"[{session_id}] " if session_id else ""
        try:
            user_input = input(f"{prefix}You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            parts = user_input.split(None, 1)
            cmd = parts[0].lower()

            if cmd == "/quit" or cmd == "/exit":
                print("Bye!")
                break

            if cmd == "/help":
                print("\nCommands:")
                for name, desc in COMMANDS.items():
                    print(f"  {name:<20} {desc}")
                print()
                continue

            if cmd == "/new":
                session_id = None
                messages = []
                print("New session started.\n")
                continue

            if cmd == "/list":
                try:
                    sessions = list_sessions()
                    _print_sessions(sessions)
                except Exception as e:
                    print(f"Error listing sessions: {e}\n")
                continue

            if cmd == "/switch":
                if len(parts) < 2:
                    print("Usage: /switch <session_id>\n")
                    continue
                sid = parts[1].strip()
                try:
                    sessions = list_sessions()
                    ids = [s["id"] for s in sessions]
                    if sid not in ids:
                        print(f"Session '{sid}' not found.\n")
                        continue
                    session_id = sid
                    messages = []
                    print(f"Switched to session {session_id}.\n")
                except Exception as e:
                    print(f"Error switching session: {e}\n")
                continue

            if cmd == "/delete":
                if len(parts) < 2:
                    print("Usage: /delete <session_id>\n")
                    continue
                sid = parts[1].strip()
                try:
                    if delete_session(sid):
                        print(f"Session '{sid}' deleted.\n")
                        if session_id == sid:
                            session_id = None
                            messages = []
                    else:
                        print(f"Session '{sid}' not found.\n")
                except Exception as e:
                    print(f"Error deleting session: {e}\n")
                continue

            if cmd == "/info":
                if session_id:
                    print(f"Current session: {session_id}\n")
                else:
                    print("No active session (will auto-create on first message).\n")
                continue

            print(f"Unknown command: {cmd}. Type /help for commands.\n")
            continue

        messages.append(ChatCompletionUserMessageParam(role="user", content=user_input))

        try:
            _send_turn(messages, session_id)
        except Exception as e:
            print(f"\nError: {e}")

        print()


if __name__ == "__main__":
    main()
