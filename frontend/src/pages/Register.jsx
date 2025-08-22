import React, { useState } from "react";
import { register } from "@/api/auth";
import { Link, useNavigate } from "react-router-dom";

export default function RegisterPage() {
  const [form, setForm] = useState({
    email: "",
    name: "",
    password: "",
    role: "user",
  });
  const [err, setErr] = useState(null);
  const [ok, setOk] = useState(false);
  const nav = useNavigate();

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function onSubmit(e) {
    e.preventDefault();
    setErr(null); setOk(false);
    try {
      await register(form);
      setOk(true);
      setTimeout(()=>nav("/login", { replace: true }), 700);
    } catch (e) {
      setErr(e?.response?.data?.detail ?? "Register failed");
    }
  }

  return (
    <div className="min-h-screen grid place-items-center p-6">
      <div className="card p-6 md:p-8 w-full max-w-lg">
        <h2 className="text-xl font-semibold mb-2">Create account</h2>
        <p className="text-sm text-slate-300 mb-6">Start discovering better books with AI.</p>

        <form onSubmit={onSubmit} className="grid gap-4">
          <input name="email" className="input" type="email" placeholder="Email" value={form.email} onChange={handleChange} required />
          <input name="name" className="input" type="text" placeholder="Name" value={form.name} onChange={handleChange} required />
          <input name="password" className="input" type="password" placeholder="Password" value={form.password} onChange={handleChange} required />
          {/* Optional: role select */}
          {/* <select name="role" value={form.role} onChange={handleChange}>
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select> */}
          <button className="btn btn-primary">Register</button>

          {ok && <div className="text-emerald-400 text-sm">Account created. Redirecting…</div>}
          {err && <div className="text-red-400 text-sm">{String(err)}</div>}

          <div className="text-sm text-slate-300">
            Already have an account?{" "}
            <Link className="underline decoration-fuchsia-400" to="/login">Sign in</Link>
          </div>
        </form>
      </div>
    </div>
  );
}
