from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request
import markdown

APP_ROOT = Path(__file__).parent
DEFAULT_OUTPUT_PATH = APP_ROOT / "data" / "terminal_output.md"
DEFAULT_INPUT_PATH = APP_ROOT / "data" / "terminal_input.md"


def _resolve_path(env_var: str, default: Path) -> Path:
    value = os.environ.get(env_var)
    if value:
        return Path(value).expanduser().resolve()
    return default


OUTPUT_FILE = _resolve_path("TERMINAL_OUTPUT_PATH", DEFAULT_OUTPUT_PATH)
INPUT_FILE = _resolve_path("TERMINAL_INPUT_PATH", DEFAULT_INPUT_PATH)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)


def read_output() -> str:
    if OUTPUT_FILE.exists():
        return OUTPUT_FILE.read_text(encoding="utf-8")
    return ""


def render_output_html() -> str:
    return markdown.markdown(read_output(), extensions=["fenced_code", "tables"])


def append_input(command: str) -> Dict[str, Any]:
    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    sanitized = command.rstrip("\n")
    with INPUT_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"{sanitized}\n")
    return {"timestamp": timestamp, "command": sanitized}


@app.route("/")
def index() -> str:
    return render_template(
        "index.html",
        output_html=render_output_html(),
        output_path=str(OUTPUT_FILE),
        input_path=str(INPUT_FILE),
    )


@app.get("/api/output")
def api_get_output():
    content = read_output()
    updated_at = None
    if OUTPUT_FILE.exists():
        updated_at = datetime.utcfromtimestamp(OUTPUT_FILE.stat().st_mtime).isoformat() + "Z"
    return jsonify({"content": content, "updated_at": updated_at})


@app.post("/api/input")
def api_post_input():
    data = request.get_json(silent=True) or {}
    command = (data.get("command") or "").strip()
    if not command:
        return jsonify({"error": "Command cannot be empty."}), 400

    entry = append_input(command)
    return jsonify({"status": "ok", "entry": entry})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
