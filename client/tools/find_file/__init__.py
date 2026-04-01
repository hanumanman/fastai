import subprocess


def find_file(query: str) -> str:
    """Find files in the current codebase using fzf."""
    try:
        result = subprocess.run(
            ["fzf", "--filter", query],
            input=subprocess.run(
                ["find", ".", "-type", "f"],
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout,
            capture_output=True,
            text=True,
            timeout=10,
        )
        matches = [
            line.strip() for line in result.stdout.strip().split("\n") if line.strip()
        ]
        matches = matches[:10]
        if not matches:
            return f"No files found matching: {query}"
        return "\n".join(matches)
    except FileNotFoundError:
        return "Error: fzf is not installed"
    except subprocess.TimeoutExpired:
        return "Error: file search timed out"
