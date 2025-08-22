import { useState } from "react";

export default function MessageInput({ onSend }) {
  const [value, setValue] = useState("");

  function handleSend() {
    const v = value.trim();
    if (!v) return;
    onSend(v);
    setValue("");
  }

  return (
    <div className="flex gap-2">
      <input
        className="input flex-1"
        placeholder="Ask for a book, genre, mood…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
      />
      <button className="btn btn-primary" onClick={handleSend}>Send</button>
    </div>
  );
}
