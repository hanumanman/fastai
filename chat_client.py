import json
import sys

import httpx

URL = "http://localhost:8000/chat"
PROMPT = "how to implement a bubble sort in rust?"


def main():
    payload = {
        "messages": [{"role": "user", "content": PROMPT}],
        "enable_reasoning": True,
    }

    with httpx.Client() as client:
        with client.stream("POST", URL, json=payload, timeout=120.0) as response:
            response.raise_for_status()
            buffer = ""
            reasoning_active = False

            for chunk in response.iter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    line, buffer = buffer.split("\n\n", 1)
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            print()
                            return
                        event = json.loads(data)
                        if event["type"] == "reasoning":
                            if not reasoning_active:
                                print("[THINKING] ", end="", flush=True)
                                reasoning_active = True
                            print(event["data"], end="", flush=True)
                        elif event["type"] == "content":
                            if reasoning_active:
                                print("\n\n[OUTPUT]\n", flush=True)
                                reasoning_active = False
                            print(event["data"], end="", flush=True)


if __name__ == "__main__":
    main()
