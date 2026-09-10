import json
import sys
from typing import TextIO

from . import commands

_COMMANDS = {
    "get_history": commands.get_history,
    "get_content": commands.get_content,
    "save_version": commands.save_version,
}


def handle_request(request: dict) -> dict:
    command_name = request.get("command")
    params = request.get("params", {})
    if command_name not in _COMMANDS:
        raise ValueError(f"Unknown command: {command_name}")
    return {"status": "success", "data": _COMMANDS[command_name](params)}


def run(input_stream: TextIO = sys.stdin, output_stream: TextIO = sys.stdout) -> None:
    for line in input_stream:
        try:
            request = json.loads(line)
            response = handle_request(request)
        except Exception as error:
            response = {
                "status": "error",
                "error": {"message": f"{type(error).__name__}: {error}"},
            }
        output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")
        output_stream.flush()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
