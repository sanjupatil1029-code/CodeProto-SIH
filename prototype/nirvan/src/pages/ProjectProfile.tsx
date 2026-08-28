import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Sparkles } from "lucide-react";
import AppShell from "../components/AppShell";
import { useApp } from "../context/AppContext";
import { businessTypes, indianStates, districtsByState } from "../data/businessTypes";
import type { BusinessSize, ProjectType } from "../types";

export default function ProjectProfile() {
  const { profile, setProfile, category } = useApp();
  const [params] = useSearchParams();
  const navigate = useNavigate();

  const preselected = params.get("type");
  const isIndustry = (id: string) => ["food", "textile", "metal", "sugar"].includes(id);

  const [companyName, setCompanyName] = useState(profile?.companyName || "");
  const [businessTypeId, setBusinessTypeId] = useState(profile?.businessTypeId || preselected || businessTypes[0].id);
  const [state, setState] = useState(profile?.state || "Maharashtra");
  const [district, setDistrict] = useState(profile?.district || districtsByState["Maharashtra"][0]);
  const [cityTaluk, setCityTaluk] = useState(profile?.cityTaluk || "");
  const [size, setSize] = useState<BusinessSize>(profile?.size || "Medium");
  const [projectType, setProjectType] = useState<ProjectType>(profile?.projectType || "New Setup");
  const [employees, setEmployees] = useState<number>(profile?.employees ?? 25);
  const [activity, setActivity] = useState(profile?.activity || "");
  const [error, setError] = useState("");

  const industryFlow = isIndustry(businessTypeId);
  const selectedBiz = businessTypes.find((b) => b.id === businessTypeId);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyName || !cityTaluk || !activity) {
      setError("Please fill in all required fields.");
      return;
    }
    setProfile({
      companyName,
      businessTypeId,
      state,
      district,
      cityTaluk,
      size,
      projectType,
      employees,
      activity,
    });
    navigate("/roadmap");
  };

  return (
    <AppShell>
      <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">Create Your Project Profile</h1>
      <p className="mt-1.5 max-w-xl text-sm text-slate-soft">
        We'll use this to work out exactly which approvals, documents and schemes apply to you.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 max-w-2xl space-y-6">
        <div className="card space-y-5 p-6">
          <h2 className="font-display text-sm font-bold uppercase tracking-wide text-slate-soft">Business Details</h2>

          <div>
            <label className="label-text">Business / Project Name *</label>
            <input className="input-field" placeholder="e.g. ABC Foods Pvt Ltd" value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
          </div>

          <div>
            <label className="label-text">
              {category === "shop" ? "Shop Type *" : category === "industry" ? "Industry / Business Type *" : "Industry / Business Type *"}
            </label>
            <select className="input-field" value={businessTypeId} onChange={(e) => setBusinessTypeId(e.target.value)}>
              {category ? (
                businessTypes.filter((b) => b.category === category).map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))
              ) : (
                <>
                  <optgroup label="Shop">
                    {businessTypes.filter((b) => b.category === "shop").map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </optgroup>
                  <optgroup label="Industry">
                    {businessTypes.filter((b) => b.category === "industry").map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </optgroup>
                </>
              )}
            </select>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label-text">State *</label>
              <select
                className="input-field"
                value={state}
                onChange={(e) => {
                  setState(e.target.value);
                  setDistrict(districtsByState[e.target.value][0]);
                }}
              >
                {indianStates.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="label-text">District *</label>
              <select className="input-field" value={district} onChange={(e) => setDistrict(e.target.value)}>
                {districtsByState[state].map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label className="label-text">City / Taluk *</label>
              <input className="input-field" placeholder="e.g. Wagholi" value={cityTaluk} onChange={(e) => setCityTaluk(e.target.value)} />
            </div>
          </div>
        </div>

        <div className="card space-y-5 p-6">
          <h2 className="font-display text-sm font-bold uppercase tracking-wide text-slate-soft">Scale &amp; Stage</h2>

          <div>
            <label className="label-text">Business Size *</label>
            <div className="grid grid-cols-3 gap-3">
              {(["Small", "Medium", "Large"] as BusinessSize[]).map((s) => (
                <button
                  type="button"
                  key={s}
                  onClick={() => setSize(s)}
                  className={`rounded-lg border px-3 py-2.5 text-sm font-semibold transition-colors ${
                    size === s ? "border-navy bg-navy text-white" : "border-navy/15 text-ink hover:bg-mist"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="label-text">Project Type *</label>
            <div className="grid grid-cols-3 gap-3">
              {(["New Setup", "Expansion", "Renewal"] as ProjectType[]).map((p) => (
                <button
                  type="button"
                  key={p}
                  onClick={() => setProjectType(p)}
                  className={`rounded-lg border px-3 py-2.5 text-sm font-semibold transition-colors ${
                    projectType === p ? "border-navy bg-navy text-white" : "border-navy/15 text-ink hover:bg-mist"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="label-text">Number of Employees *</label>
            <input
              type="number"
              min={1}
              className="input-field"
              value={employees}
              onChange={(e) => setEmployees(Number(e.target.value))}
            />
            <p className="mt-1 text-xs text-slate-soft">Employee count affects labour registration & factory licence applicability.</p>
          </div>

          <div>
            <label className="label-text">
              {industryFlow ? "Manufacturing Activity *" : "Business Activity *"}
            </label>
            <textarea
              className="input-field min-h-[80px] resize-none"
              placeholder={
                industryFlow
                  ? `e.g. Processing & packaging of ${selectedBiz?.name.toLowerCase()} products`
                  : `e.g. Retail sale of ${selectedBiz?.name.toLowerCase()} items`
              }
              value={activity}
              onChange={(e) => setActivity(e.target.value)}
            />
          </div>
        </div>

        {error && <p className="text-sm font-medium text-danger">{error}</p>}

        <button type="submit" className="btn-accent w-full sm:w-auto">
          <Sparkles size={16} /> Generate My Approval Roadmap
        </button>
      </form>
    </AppShell>
  );
}
