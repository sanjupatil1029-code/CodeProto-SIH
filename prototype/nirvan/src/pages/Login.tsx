import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Compass, LogIn, Sparkles } from "lucide-react";
import { useApp } from "../context/AppContext";

export default function Login() {
  const { login } = useApp();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please enter both email/username and password.");
      return;
    }
    login(email);
    navigate("/dashboard");
  };

  const handleDemo = () => {
    login("demo@NIRVAAN.gov.in", "Demo User");
    navigate("/dashboard");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-hero-grid [background-size:22px_22px] bg-mist px-4">
      <div className="w-full max-w-md">
        <Link to="/" className="mb-8 flex items-center justify-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-navy text-white">
            <Compass size={18} />
          </span>
          <span className="font-display text-lg font-bold tracking-tight text-navy">NIRVAAN</span>
        </Link>

        <div className="card p-8">
          <h1 className="font-display text-2xl font-bold text-ink">Welcome Back</h1>
          <p className="mt-1 text-sm text-slate-soft">Log in to continue your approval journey.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="label-text">Email / Username</label>
              <input
                type="text"
                className="input-field"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label className="label-text">Password</label>
              <input
                type="password"
                className="input-field"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {error && <p className="text-sm font-medium text-danger">{error}</p>}
            <button type="submit" className="btn-primary w-full">
              <LogIn size={16} /> Login
            </button>
          </form>

          <button
            onClick={handleDemo}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-saffron/50 bg-saffron/5 px-5 py-2.5 text-sm font-semibold text-saffron-dark hover:bg-saffron/10"
          >
            <Sparkles size={15} /> Continue with Demo Login
          </button>

          <p className="mt-6 text-center text-sm text-slate-soft">
            New to NIRVAAN?{" "}
            <Link to="/signup" className="font-semibold text-navy hover:underline">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
