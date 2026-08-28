import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Compass, LogIn, Sparkles, Loader2 } from "lucide-react";
import { useApp } from "../context/AppContext";

export default function Login() {
  const { login } = useApp();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await login(email, undefined, password);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message || "Invalid credentials or user not found. Please sign up if you don't have an account.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setLoading(true);
    setError("");
    try {
      await login("demo_entrepreneur@nirvaan.gov.in", "Demo Entrepreneur", "Password123!");
      navigate("/dashboard");
    } catch (err) {
      // If demo user doesn't exist on DB, attempt auto-signup
      try {
        const { register } = useApp() as any;
        await register("demo_entrepreneur@nirvaan.gov.in", "Password123!", "Demo Entrepreneur");
        navigate("/dashboard");
      } catch {
        setError("Could not complete demo login. Please try creating a new account.");
      }
    } finally {
      setLoading(false);
    }
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
          <p className="mt-1 text-sm text-slate-soft">Log in to authenticate with NIRVAAN Backend API.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="label-text">Email Address</label>
              <input
                type="email"
                required
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
                required
                className="input-field"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {error && (
              <div className="rounded-lg bg-rose-50 p-3 text-xs font-semibold text-rose-700 border border-rose-200">
                {error}
              </div>
            )}
            <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-50">
              {loading ? <Loader2 size={16} className="animate-spin" /> : <LogIn size={16} />}
              {loading ? "Authenticating with Backend..." : "Login"}
            </button>
          </form>

          <button
            onClick={handleDemo}
            disabled={loading}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-saffron/50 bg-saffron/5 px-5 py-2.5 text-sm font-semibold text-saffron-dark hover:bg-saffron/10 disabled:opacity-50"
          >
            <Sparkles size={15} /> Continue with Demo Account
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
