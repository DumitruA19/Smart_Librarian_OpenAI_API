// frontend/src/pages/Chat.jsx
import React, { useEffect, useRef, useState } from "react";
import { me } from "@/api/auth";
import { sendChat } from "../api/chat";
import ChatMessage from "@/components/ChatMessage";
import MessageInput from "@/components/MessageInput";

export default function ChatPage() {
  const [convId, setConvId] = useState(undefined);
  const [msgs, setMsgs] = useState([
    { role: "assistant", content: "Hey! Tell me what kind of book you want 📚✨" },
  ]);
  const [loading, setLoading] = useState(false);
  const listRef = useRef(null);

  useEffect(() => {
    me().catch(() => (window.location.href = "/login"));
  }, []);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [msgs.length]);

  useEffect(() => {
    const savedConvId = localStorage.getItem("convId");
    if (savedConvId) setConvId(savedConvId);
  }, []);

  async function onSend(text) {
    const userMsg = { role: "user", content: text };
    setMsgs((m) => [...m, userMsg]);
    setLoading(true);

    try {
      const res = await sendChat({
        message: text,               // <-- OBLIGATORIU
        conversationId: convId,      // <-- opțional, backend creează dacă lipsește
        // metadata: { genre: { $eq: "fantasy" }, lang: { $eq: "ro" } }, // opțional
      });

      setConvId(res.conversation_id);
      localStorage.setItem("convId", res.conversation_id);
      setMsgs((m) => [...m, { role: "assistant", content: res.answer }]);
    } catch (e) {
      // afișează motivul 422 din server dacă există
      const serverDetail =
        e?.response?.data?.detail ||
        e?.message ||
        "Chat error";
      setMsgs((m) => [...m, { role: "assistant", content: `⚠️ ${serverDetail}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container py-6 grid gap-4 h-[calc(100vh-64px)]">
      <div ref={listRef} className="card p-4 overflow-y-auto">
        <div className="grid gap-3">
          {msgs.map((m, i) => <ChatMessage key={i} role={m.role} content={m.content} />)}
          {loading && <ChatMessage role="assistant" content="Typing..." />}
        </div>
      </div>

      <div className="card p-3 md:p-4 sticky bottom-4">
        <div className="bg-gradient-to-tr from-cyan-400/10 via-fuchsia-500/10 to-emerald-400/10 rounded-[14px] p-3">
          <MessageInput onSend={onSend} disabled={loading} />
          <div className="mt-2 text-xs text-slate-300">
            Tip: Try “dystopian classic with social critique” or “cozy fantasy with found family”.
          </div>
        </div>
      </div>
    </div>
  );
}
