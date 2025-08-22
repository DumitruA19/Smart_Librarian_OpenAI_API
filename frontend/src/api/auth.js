import { api } from "./client";

export async function register(payload) {
  const { data } = await api.post("/auth/register", payload);
  return data;
}

export async function login(email, password) {
  const { data } = await api.post("/auth/login", { email, password });
  localStorage.setItem("access_token", data.access_token); // asigură-te că ai această linie!
  return data;
}

export async function me() {
  const { data } = await api.get("/auth/me");
  return data; // { id, email, name?, role, created_at }
}

export function logout() {
  localStorage.removeItem("access_token");
}
