from client import run_conversation


def main() -> None:
    print("FastAI Chat Client (type 'quit' or 'exit' to leave)\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("Bye!")
            break

        run_conversation(user_input)
        print()


if __name__ == "__main__":
    main()
