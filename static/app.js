const outputContainer = document.getElementById("output");
const statusIndicator = document.getElementById("output-status");
const form = document.getElementById("command-form");
const textarea = document.getElementById("command-input");
const clearButton = document.getElementById("clear-btn");

let lastContent = outputContainer?.innerText ?? "";
let isFetching = false;

function setStatus(text, state = "idle") {
  statusIndicator.textContent = text;
  statusIndicator.dataset.state = state;
}

async function fetchOutput() {
  if (isFetching) return;
  isFetching = true;
  try {
    const response = await fetch("/api/output", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const { content = "", updated_at: updatedAt } = payload;
    if (content !== lastContent) {
      const shouldStickToBottom =
        Math.abs(
          outputContainer.scrollHeight -
            outputContainer.scrollTop -
            outputContainer.clientHeight
        ) < 40;

      outputContainer.innerHTML = window.marked.parse(content ?? "");
      lastContent = content;

      if (shouldStickToBottom) {
        outputContainer.scrollTop = outputContainer.scrollHeight;
      }
    }
    if (updatedAt) {
      setStatus(`Updated ${new Date(updatedAt).toLocaleTimeString()}`, "ok");
    } else {
      setStatus("Awaiting output…", "idle");
    }
  } catch (error) {
    console.error("Failed to fetch output", error);
    setStatus("Connection lost", "error");
  } finally {
    isFetching = false;
  }
}

async function submitCommand(command) {
  const body = JSON.stringify({ command });
  const response = await fetch("/api/input", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Unknown" }));
    throw new Error(error.error ?? "Unable to send command");
  }

  return response.json();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const command = textarea.value.trim();
  if (!command) return;
  setStatus("Sending…", "pending");
  textarea.disabled = true;
  try {
    await submitCommand(command);
    textarea.value = "";
    setStatus("Command sent", "ok");
  } catch (error) {
    console.error(error);
    setStatus(error.message, "error");
  } finally {
    textarea.disabled = false;
    textarea.focus();
  }
});

textarea.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
    event.preventDefault();
    form.requestSubmit();
  }
});

clearButton.addEventListener("click", () => {
  textarea.value = "";
  textarea.focus();
});

setInterval(fetchOutput, 1000);
fetchOutput();
