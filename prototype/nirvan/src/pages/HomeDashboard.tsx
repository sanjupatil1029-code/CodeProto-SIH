import { useNavigate } from "react-router-dom";
import { Store, Factory, ArrowRight } from "lucide-react";
import AppShell from "../components/AppShell";
import { useApp } from "../context/AppContext";

export default function HomeDashboard() {
  const { user, profile } = useApp();
  const navigate = useNavigate();

  return (
    <AppShell hideProfileBar>
      <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">
        Welcome to NIRVAAN{user?.name ? `, ${user.name.split(" ")[0]}` : ""}
      </h1>
      <p className="mt-1.5 text-sm text-slate-soft">
        Choose your business category to begin your approval journey.
      </p>

      {profile && (
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-xl2 border border-navy/[0.06] bg-white p-5 shadow-card">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-soft">Active project</p>
            <p className="font-display text-lg font-bold text-ink">{profile.companyName}</p>
          </div>
          <button onClick={() => navigate("/roadmap")} className="btn-primary !px-4 !py-2 text-sm">
            View Roadmap <ArrowRight size={15} />
          </button>
        </div>
      )}

      <div className="mt-10 grid gap-6 sm:grid-cols-2">
        <div className="card flex flex-col p-6">
          <span className="flex h-14 w-14 items-center justify-center rounded-xl2 bg-lavender text-indigo">
            <Store size={26} />
          </span>
          <h2 className="mt-4 font-display text-lg font-bold text-ink">Shop</h2>
          <p className="mt-1.5 text-sm text-slate-soft">
            Jewellery shops, hotels, general stores, medical stores and other retail businesses.
          </p>
          <button onClick={() => navigate("/select/shop")} className="btn-secondary mt-5 w-full">
            Browse Shop Types <ArrowRight size={15} />
          </button>
        </div>

        <div className="card flex flex-col p-6">
          <span className="flex h-14 w-14 items-center justify-center rounded-xl2 bg-saffron/10 text-saffron-dark">
            <Factory size={26} />
          </span>
          <h2 className="mt-4 font-display text-lg font-bold text-ink">Industry</h2>
          <p className="mt-1.5 text-sm text-slate-soft">
            Food processing, textile, metal & engineering, sugar and other manufacturing units.
          </p>
          <button onClick={() => navigate("/select/industry")} className="btn-secondary mt-5 w-full">
            Browse Industry Types <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </AppShell>
  );
}
