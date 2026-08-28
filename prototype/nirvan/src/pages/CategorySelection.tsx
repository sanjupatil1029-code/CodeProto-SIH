import { useNavigate, useParams } from "react-router-dom";
import { useEffect } from "react";
import AppShell from "../components/AppShell";
import BusinessCard from "../components/BusinessCard";
import { businessTypes } from "../data/businessTypes";
import { useApp } from "../context/AppContext";

export default function CategorySelection() {
  const { category } = useParams<{ category: "shop" | "industry" }>();
  const { setCategory } = useApp();
  const navigate = useNavigate();

  useEffect(() => {
    if (category === "shop" || category === "industry") setCategory(category);
  }, [category]);

  const items = businessTypes.filter((b) => b.category === category);
  const title = category === "shop" ? "Select Your Business" : "Select Your Industry";

  return (
    <AppShell>
      <button onClick={() => navigate("/dashboard")} className="text-sm font-semibold text-slate-soft hover:text-navy">
        ← Back to Dashboard
      </button>
      <h1 className="mt-3 font-display text-3xl font-extrabold tracking-tight text-navy">{title}</h1>
      <p className="mt-1.5 text-sm text-slate-soft">
        Pick the option that best matches what you're setting up. You can refine details on the next step.
      </p>

      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((biz) => (
          <BusinessCard key={biz.id} biz={biz} onSelect={() => navigate(`/project?type=${biz.id}`)} />
        ))}
      </div>
    </AppShell>
  );
}
