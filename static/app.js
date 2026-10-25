const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const messages = document.getElementById("messages");
const provider = document.getElementById("provider");
const statusText = document.getElementById("status");
const send = document.getElementById("send");

function addMessage(text, type) {
  const item = document.createElement("div");
  item.className = `bubble ${type}`;
  item.textContent = text;
  messages.appendChild(item);
  return item;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = input.value.trim();
  if (!message) return;

  addMessage(message, "user");
  input.value = "";
  send.disabled = true;
  statusText.textContent = "AI উত্তর তৈরি করছে...";

  const waiting = addMessage("অপেক্ষা করো...", "ai");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        message,
        provider: provider.value
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Request failed");
    }

    waiting.textContent =
      `[${data.provider}] ${data.reply}`;

    statusText.textContent = "Ready";
  } catch (error) {
    waiting.textContent = "সমস্যা: " + error.message;
    statusText.textContent = "Error";
  } finally {
    send.disabled = false;
    messages.scrollTop = messages.scrollHeight;
  }
});
