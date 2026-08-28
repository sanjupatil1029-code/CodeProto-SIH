import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Compass, UserPlus } from "lucide-react";
import { useApp } from "../context/AppContext";

export default function Signup() {
  const { login } = useApp();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "", confirm: "" });
  const [error, setError] = useState("");

  const update = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.phone || !form.password) {
      setError("Please fill in all fields.");
      return;
    }
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    login(form.email, form.name);
    navigate("/dashboard");
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
              <label className="label-text">Full Name</label>
              <input className="input-field" placeholder="Rahul Sharma" value={form.name} onChange={(e) => update("name", e.target.value)} />
            </div>
            <div>
              <label className="label-text">Email</label>
              <input className="input-field" placeholder="you@company.com" value={form.email} onChange={(e) => update("email", e.target.value)} />
            </div>
            <div>
              <label className="label-text">Phone Number</label>
              <input className="input-field" placeholder="98765 43210" value={form.phone} onChange={(e) => update("phone", e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label-text">Password</label>
                <input type="password" className="input-field" placeholder="••••••••" value={form.password} onChange={(e) => update("password", e.target.value)} />
              </div>
              <div>
                <label className="label-text">Confirm Password</label>
                <input type="password" className="input-field" placeholder="••••••••" value={form.confirm} onChange={(e) => update("confirm", e.target.value)} />
              </div>
            </div>
            {error && <p className="text-sm font-medium text-danger">{error}</p>}
            <button type="submit" className="btn-primary w-full">
              <UserPlus size={16} /> Create Account
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
