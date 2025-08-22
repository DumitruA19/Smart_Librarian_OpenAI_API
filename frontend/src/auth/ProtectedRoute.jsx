// src/auth/ProtectedRoute.jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-6 text-slate-300">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
