import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { logout } from "@/api/auth";

export default function Navbar() {
  const { user } = useAuth();
  const nav = useNavigate();

  function onLogout() {
    logout();
    nav("/login", { replace: true });
  }

  return (
    <header className="sticky top-0 z-40 backdrop-blur bg-slate-950/60 border-b border-white/10">
      <div className="container h-16 flex items-center justify-between">
        <Link to="/chat" className="flex items-center gap-3">
          <div className="size-9 rounded-[14px] bg-gradient-to-tr from-cyan-400 to-fuchsia-500 grid place-items-center">
            <span className="font-extrabold text-slate-950">SL</span>
          </div>
          <div className="leading-tight">
            <div className="font-semibold tracking-wide">Smart Librarian</div>
            <div className="badge">AI book assistant</div>
          </div>
        </Link>

        <nav className="flex items-center gap-2">
          <Link to="/chat" className="btn btn-ghost">Chat</Link>
          {user && <button onClick={onLogout} className="btn btn-primary">Logout</button>}
        </nav>
      </div>
    </header>
  );
}
