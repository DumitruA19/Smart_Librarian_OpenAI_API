import axios from "axios";
import { useEffect } from "react";

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
export const api = axios.create({ baseURL });

// attach JWT if present
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 401 → redirect to /login
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ----- Auth -----
export async function register(email, password) {
  const { data } = await api.post("/auth/register", { email, password });
  return data;
}

export async function login(email, password) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error("Login failed");
  return await res.json();
}

export async function me() {
  const { data } = await api.get("/auth/me");
  return data;
}

export async function getMe(token) {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Not authenticated");
  return await res.json();
}

// ----- Chat -----
export async function sendMessage(message, conversationId) {
  const body = { message };
  if (conversationId) body.conversation_id = conversationId;
  const { data } = await api.post("/chat", body);
  return data; // { conversation_id, answer, title?, reason? }
}

// ----- Books -----
export async function getBookTitles(token) {
  const res = await fetch(`${API_URL}/books/titles`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch book titles");
  return await res.json();
}

export function useBookTitles(token, setTitles) {
  useEffect(() => {
    async function fetchTitles() {
      try {
        const data = await getBookTitles(token); // asigură-te că backend-ul returnează toate titlurile
        setTitles(data.titles || []);
      } catch (err) {
        setTitles([]);
      }
    }
    fetchTitles();
  }, [token, setTitles]);
}
