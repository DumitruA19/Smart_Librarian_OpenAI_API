import { useEffect, useState } from "react";
import { login, me } from "@/api/auth";
import { useAuth } from "@/auth/AuthContext";
import { useNavigate, Link } from "react-router-dom";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(false);
  const { refresh } = useAuth();
  const nav = useNavigate();

  useEffect(() => {
    me().then(() => nav("/chat", { replace: true })).catch(() => {});
  }, [nav]);

  async function onSubmit(e) {
    e.preventDefault();
    setErr(null); setLoading(true);
    try {
      await login(email, password);
      await refresh();
      nav("/chat", { replace: true });
    } catch (e) {
      setErr(e?.response?.data?.detail ?? "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center p-6">
      <div className="container">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          {/* Side hero cu titlu & text frumos */}
          <section className="hidden md:block">
            <h1 className="text-4xl md:text-5xl font-black leading-tight">
              Welcome back <span className="inline-block">👋</span>
            </h1>
            <p className="text-slate-300 mt-4 text-lg max-w-md">
              Sign in to get <span className="text-cyan-300 font-semibold">vivid</span>, AI-powered book recommendations,
              tuned to your mood and favorite genres.
            </p>
          </section>

          {/* Card login */}
          <section className="card p-6 md:p-8">
            <h2 className="text-xl font-semibold mb-2">Sign in</h2>
            <p className="text-sm text-slate-300 mb-6">Use your account to access the chat.</p>

            <form onSubmit={onSubmit} className="grid gap-4">
              <input
                className="input"
                placeholder="Email"
                type="email"
                value={email}
                onChange={(e)=>setEmail(e.target.value)}
              />
              <input
                className="input"
                placeholder="Password"
                type="password"
                value={password}
                onChange={(e)=>setPassword(e.target.value)}
              />

              <button className="btn btn-primary" disabled={loading}>
                {loading ? "Signing in…" : "Sign in"}
              </button>

              {err && <div className="text-red-400 text-sm">{String(err)}</div>}

              <div className="text-sm text-slate-300">
                Don’t have an account?{" "}
                <Link className="underline decoration-cyan-400" to="/register">Create one</Link>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
