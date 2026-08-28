import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Compass, UserPlus, Loader2, CheckCircle2 } from "lucide-react";
import { useApp } from "../context/AppContext";

export default function Signup() {
  const { register } = useApp();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.password) {
      setError("Please fill in all required fields.");
      return;
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }

    setError("");
    setSuccess("");
    setLoading(true);
    try {
      await register(form.email, form.password, form.name);
      setSuccess("Account created successfully! Redirecting to login page in 3 seconds...");
      setTimeout(() => {
        navigate("/login");
      }, 3000);
    } catch (err: any) {
      setError(err.message || "Registration failed. This email may already be registered.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-hero-grid [background-size:22px_22px] bg-mist px-4 py-10">
      <div className="w-full max-w-md">
        <Link to="/" className="mb-8 flex items-center justify-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-navy text-white">
            <Compass size={18} />
          </span>
          <span className="font-display text-lg font-bold tracking-tight text-navy">NIRVAAN</span>
        </Link>

        <div className="card p-8">
          <h1 className="font-display text-2xl font-bold text-ink">Create your NIRVAAN account</h1>
          <p className="mt-1 text-sm text-slate-soft">Start your guided compliance journey in minutes.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="label-text">Full Name *</label>
              <input required disabled={!!success} className="input-field disabled:opacity-60" placeholder="Rahul Sharma" value={form.name} onChange={(e) => update("name", e.target.value)} />
            </div>
            <div>
              <label className="label-text">Email Address *</label>
              <input required disabled={!!success} type="email" className="input-field disabled:opacity-60" placeholder="you@company.com" value={form.email} onChange={(e) => update("email", e.target.value)} />
            </div>
            <div>
              <label className="label-text">Phone Number</label>
              <input
                disabled={!!success}
                type="tel"
                maxLength={10}
                className="input-field disabled:opacity-60"
                placeholder="9876543210"
                value={form.phone}
                onChange={(e) => update("phone", e.target.value.replace(/\D/g, "").slice(0, 10))}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label-text">Password *</label>
                <input required disabled={!!success} type="password" className="input-field disabled:opacity-60" placeholder="••••••••" value={form.password} onChange={(e) => update("password", e.target.value)} />
              </div>
              <div>
                <label className="label-text">Confirm Password *</label>
                <input required disabled={!!success} type="password" className="input-field disabled:opacity-60" placeholder="••••••••" value={form.confirm} onChange={(e) => update("confirm", e.target.value)} />
              </div>
            </div>
            {error && (
              <div className="rounded-lg bg-rose-50 p-3 text-xs font-semibold text-rose-700 border border-rose-200">
                {error}
              </div>
            )}
            {success && (
              <div className="rounded-lg bg-emerald-50 p-3.5 text-xs font-semibold text-emerald-800 border border-emerald-200 flex items-center gap-2">
                <CheckCircle2 size={18} className="text-emerald-600 flex-shrink-0" />
                <span>{success}</span>
              </div>
            )}
            <button type="submit" disabled={loading || !!success} className="btn-primary w-full disabled:opacity-50">
              {loading ? <Loader2 size={16} className="animate-spin" /> : <UserPlus size={16} />}
              {loading ? "Creating Account..." : "Create Account"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-soft">
            Already have an account?{" "}
            <Link to="/login" className="font-semibold text-navy hover:underline">
              Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
