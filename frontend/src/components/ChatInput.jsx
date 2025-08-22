"use client";
import { useState } from "react";
import { sendChat } from "../api/chat";

export default function MessageInput({ onSend }) {
  const [value, setValue] = useState("");

  async function handleSend() {
    const v = value.trim();
    if (!v) return;

    const history = [
      { role: "user", content: "Your new message" }
      // ...previous messages
    ];
    const response = await sendChat(history);

    onSend(v);
    setValue("");
  }

  return (
    <div className="flex gap-2">
      <input
        className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 h-12 outline-none focus:ring-2 focus:ring-accent-sky/50"
        placeholder="Ask for a book..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
      />
      <button
        className="h-12 px-4 rounded-xl bg-accent-sky/20 text-sky-200 border border-sky-500/20 hover:bg-accent-sky/30 transition"
        onClick={handleSend}
      >
        Send
      </button>
    </div>
  );
}
