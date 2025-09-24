# Ghostty Terminal Web Bridge

This project provides a lightweight Flask application that mirrors a terminal
session through a web interface. The UI polls a Markdown file for output (to
simulate streaming) and writes submitted prompts or commands back to another
Markdown file that you can forward into a Ghostty session on macOS.

## Features

- Split-pane dashboard with live terminal output rendered from Markdown.
- Command composer that writes to `data/terminal_input.md`.
- REST API endpoints for fetching output and sending new commands.
- Example macOS bridge script that forwards commands to any interactive CLI
  program and captures its output.

## Getting started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Start the web server**

   ```bash
   python app.py
   ```

   The UI will be available at <http://127.0.0.1:5000>. By default the app reads
   from `data/terminal_output.md` and writes to `data/terminal_input.md`. You can
   override these paths with the `TERMINAL_OUTPUT_PATH` and
   `TERMINAL_INPUT_PATH` environment variables.

3. **Connect a Ghostty session**

   On macOS you can use the helper script to connect the browser UI with the
   terminal session that runs your AI agent:

   ```bash
   ./scripts/ghostty_bridge.py -- python -m your_cli_agent
   ```

   The script tails `data/terminal_input.md` for new prompts and sends them to
   the spawned process. All stdout/stderr is appended to
   `data/terminal_output.md`, allowing the browser to display it in near real
   time.

   > Tip: make sure the script is executable with `chmod +x scripts/ghostty_bridge.py`.

4. **Use within Ghostty**

   - Launch Ghostty and start the bridge script in a tab or split pane.
   - In another pane run whatever background processes you need for your agent.
   - Use the browser UI to send prompts and monitor the live output stream.

## API overview

- `GET /api/output` — returns JSON `{ "content": "...", "updated_at": "..." }`.
- `POST /api/input` — accepts `{ "command": "..." }` and appends it to the input file.

These endpoints back the web UI but can also be automated from other tools.

## Customisation

- Tweak the polling interval or UI behaviour in `static/app.js`.
- Update the layout or styling via `templates/index.html` and `static/styles.css`.
- Point the bridge script at different files or commands via CLI flags.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for
details.
