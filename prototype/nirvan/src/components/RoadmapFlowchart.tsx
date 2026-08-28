import { useNavigate } from "react-router-dom";
import { CheckCircle2, ArrowRight, Circle, AlertTriangle, FileCheck2 } from "lucide-react";
import type { ApprovalDef, ApprovalRuntime } from "../types";
import { STATUS_META } from "./StatusBadge";

interface Props {
  levels: ApprovalDef[][];
  runtimes: Record<string, ApprovalRuntime>;
}

const NODE_GLYPH: Record<string, { icon: React.ComponentType<{ size?: number; className?: string }>; ring: string; dot: string }> = {
  approved: { icon: CheckCircle2, ring: "border-success bg-success text-white", dot: "bg-success" },
  under_review: { icon: ArrowRight, ring: "border-saffron-dark bg-white text-saffron-dark", dot: "bg-saffron" },
  submitted: { icon: ArrowRight, ring: "border-indigo bg-white text-indigo", dot: "bg-indigo" },
  inspection_scheduled: { icon: ArrowRight, ring: "border-warn bg-white text-warn", dot: "bg-warn" },
  query_raised: { icon: AlertTriangle, ring: "border-danger bg-white text-danger", dot: "bg-danger" },
  documents_required: { icon: AlertTriangle, ring: "border-warn bg-white text-warn", dot: "bg-warn" },
  renewal_due: { icon: AlertTriangle, ring: "border-warn bg-white text-warn", dot: "bg-warn" },
  ready: { icon: Circle, ring: "border-indigo bg-white text-indigo", dot: "bg-indigo" },
  not_started: { icon: Circle, ring: "border-slate-300 bg-white text-slate-300", dot: "bg-slate-300" },
};

/** Simple, mobile-friendly vertical step-by-step roadmap. Steps follow dependency order (earlier levels first). */
export default function RoadmapFlowchart({ levels, runtimes }: Props) {
  const navigate = useNavigate();
  const steps = levels.flat();

  return (
    <div className="relative">
      {steps.map((approval, idx) => {
        const runtime = runtimes[approval.id];
        const status = runtime?.status || "not_started";
        const glyph = NODE_GLYPH[status] || NODE_GLYPH.not_started;
        const Icon = glyph.icon;
        const isLast = idx === steps.length - 1;

        return (
          <div key={approval.id} className="relative flex gap-4">
            <div className="flex flex-col items-center">
              <div
                className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border-2 ${glyph.ring}`}
              >
                <Icon size={17} />
              </div>
              {!isLast && <div className="w-0.5 flex-1 bg-navy/10" style={{ minHeight: 24 }} />}
            </div>

            <div
              onClick={() => navigate(`/roadmap/${approval.id}`)}
              className={`card relative mb-5 flex-1 cursor-pointer p-4 transition-shadow hover:shadow-cardHover ${
                status === "query_raised" ? "border-danger/40" : ""
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <h4 className="font-display text-sm font-bold leading-snug text-ink">
                  Step {idx + 1}: {approval.name}
                </h4>
                {approval.inspectionRequired && (
                  <span className="pill flex-shrink-0 bg-lavender text-[10px] text-indigo">Inspection</span>
                )}
              </div>
              <p className="mt-1 text-xs font-semibold" style={{ color: "#5B6482" }}>
                {STATUS_META[status].label}
              </p>
              {runtime?.documentsReady && (
                <p className="mt-2 flex items-center gap-1.5 text-xs font-semibold text-success">
                  <FileCheck2 size={13} /> Documents verified
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
