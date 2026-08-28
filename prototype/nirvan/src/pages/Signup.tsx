import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Compass, UserPlus, Loader2 } from "lucide-react";
import { useApp } from "../context/AppContext";

export default function Signup() {
  const { register } = useApp();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "", confirm: "" });
  const [error, setError] = useState("");
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
    setLoading(true);
    try {
      await register(form.email, form.password, form.name);
      navigate("/dashboard");
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
          <p className="mt-1 text-sm text-slate-soft">Sign up to register with backend database.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="label-text">Full Name *</label>
              <input required className="input-field" placeholder="Rahul Sharma" value={form.name} onChange={(e) => update("name", e.target.value)} />
            </div>
            <div>
              <label className="label-text">Email Address *</label>
              <input required type="email" className="input-field" placeholder="you@company.com" value={form.email} onChange={(e) => update("email", e.target.value)} />
            </div>
            <div>
              <label className="label-text">Phone Number</label>
              <input className="input-field" placeholder="98765 43210" value={form.phone} onChange={(e) => update("phone", e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label-text">Password *</label>
                <input required type="password" className="input-field" placeholder="••••••••" value={form.password} onChange={(e) => update("password", e.target.value)} />
              </div>
              <div>
                <label className="label-text">Confirm Password *</label>
                <input required type="password" className="input-field" placeholder="••••••••" value={form.confirm} onChange={(e) => update("confirm", e.target.value)} />
              </div>
            </div>
            {error && (
              <div className="rounded-lg bg-rose-50 p-3 text-xs font-semibold text-rose-700 border border-rose-200">
                {error}
              </div>
            )}
            <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-50">
              {loading ? <Loader2 size={16} className="animate-spin" /> : <UserPlus size={16} />}
              {loading ? "Creating Account on Backend..." : "Create Account"}
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
