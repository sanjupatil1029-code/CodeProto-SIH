import { ArrowRight } from "lucide-react";
import DynamicIcon from "./DynamicIcon";
import type { BusinessTypeDef } from "../types";

export default function BusinessCard({
  biz,
  onSelect,
}: {
  biz: BusinessTypeDef;
  onSelect: () => void;
}) {
  return (
    <div className="card group flex flex-col p-6 transition-shadow hover:shadow-cardHover">
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-navy to-indigo text-white shadow-card">
        <DynamicIcon name={biz.icon} size={22} />
      </div>
      <h3 className="mt-4 font-display text-base font-bold text-ink">{biz.name}</h3>
      <p className="mt-1.5 flex-1 text-sm leading-relaxed text-slate-soft">{biz.description}</p>
      <button
        onClick={onSelect}
        className="mt-5 flex items-center justify-between rounded-lg bg-mist px-3.5 py-2.5 text-sm font-semibold text-navy group-hover:bg-lavender transition-colors"
      >
        Select
        <ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" />
      </button>
    </div>
  );
}
