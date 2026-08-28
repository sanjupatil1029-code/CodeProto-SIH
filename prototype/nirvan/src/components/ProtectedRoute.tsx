import { Navigate } from "react-router-dom";
import { useApp } from "../context/AppContext";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user } = useApp();
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function ProjectRequired({ children }: { children: React.ReactNode }) {
  const { profile } = useApp();
  if (!profile) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}
