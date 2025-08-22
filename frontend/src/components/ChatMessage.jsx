export default function ChatMessage({ role, content }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] md:max-w-[70%] p-3 md:p-4 rounded-[14px] border whitespace-pre-wrap
          ${isUser
            ? "bg-gradient-to-tr from-cyan-400/20 to-fuchsia-500/20 border-white/15 text-slate-100"
            : "bg-white/10 border-white/15 text-slate-100"
          }`}
      >
        {content}
      </div>
    </div>
  );
}
