#!/usr/bin/env python3
"""Bridge commands between the web UI and a local CLI process.

This helper is intended for macOS + Ghostty workflows where you run your
interactive AI agent inside Ghostty and want the browser UI to feed it prompts
and receive streaming output.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("data/terminal_input.md"),
        help="Path that the web UI writes commands to.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("data/terminal_output.md"),
        help="Path that will collect terminal output in Markdown.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run (for example: python -m cli_agent).",
    )
    return parser


async def append(path: Path, text: str, lock: asyncio.Lock) -> None:
    async with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(text)


async def tail_input(
    input_path: Path,
    stdin: asyncio.StreamWriter,
    output_path: Path,
    lock: asyncio.Lock,
) -> None:
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.touch(exist_ok=True)
    last_size = input_path.stat().st_size

    while True:
        await asyncio.sleep(0.5)
        size = input_path.stat().st_size
        if size < last_size:
            # File truncated
            last_size = 0
        if size == last_size:
            continue
        with input_path.open("r", encoding="utf-8") as handle:
            handle.seek(last_size)
            data = handle.read()
        last_size = size
        for raw_line in data.splitlines():
            command = raw_line.strip()
            if not command:
                continue
            timestamp = datetime.now().strftime("%H:%M:%S")
            await append(output_path, f"\n$ {command}    # {timestamp}\n", lock)
            stdin.write(command.encode("utf-8") + b"\n")
            await stdin.drain()


async def pipe_stream(
    stream: asyncio.StreamReader,
    output_path: Path,
    lock: asyncio.Lock,
) -> None:
    while True:
        chunk = await stream.read(1024)
        if not chunk:
            break
        await append(output_path, chunk.decode("utf-8", errors="replace"), lock)


async def run_bridge(command: Sequence[str], input_path: Path, output_path: Path) -> int:
    if not command:
        raise SystemExit("Please specify the command to run after '--'.")

    lock = asyncio.Lock()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("# Ghostty Web Bridge\n\n````text\n", encoding="utf-8")

    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    assert process.stdin and process.stdout and process.stderr

    tasks = [
        asyncio.create_task(tail_input(input_path, process.stdin, output_path, lock)),
        asyncio.create_task(pipe_stream(process.stdout, output_path, lock)),
        asyncio.create_task(pipe_stream(process.stderr, output_path, lock)),
    ]

    try:
        return_code = await process.wait()
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await append(output_path, "````\n", lock)

    return return_code


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("You must provide a command to run after '--'.")
    exit_code = asyncio.run(run_bridge(command, args.input.expanduser(), args.output.expanduser()))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
