// frontend/src/api/chat.js
import { api } from "./client";

/**
 * @param {object} args
 * @param {string} args.message
 * @param {string|number=} args.conversationId
 * @param {object=} args.where        // filtru RAG (ex: { lang: "ro" })
 */
export async function sendChat({ message, conversationId, where } = {}) {
  if (!message || !message.trim()) throw new Error("Message is required");

  const payload = {
    message,
    ...(conversationId ? { conversation_id: conversationId } : {}),
    ...(where ? { where } : {}),
  };

  const res = await api.post("/chat", payload, {
    headers: { "Content-Type": "application/json" },
  });
  return res.data;
}
