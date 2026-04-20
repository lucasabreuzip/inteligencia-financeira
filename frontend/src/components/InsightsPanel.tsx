import { clsx } from "clsx";
import { Sparkles, ShieldAlert, AlertTriangle, Info } from "lucide-react";

import type { AIInsights, Classification, Severity } from "@/lib/types";

interface Props {
  insights: AIInsights;
}

const CLASSIF_TONE: Record<Classification, { label: string; badge: string }> = {
  saudavel: {
    label: "Saudável",
    badge: "bg-emerald-100 text-emerald-700 border-emerald-200",
  },
  atencao: {
    label: "Atenção",
    badge: "bg-amber-100 text-amber-700 border-amber-200",
  },
  critico: {
    label: "Crítico",
    badge: "bg-red-100 text-red-700 border-red-200",
  },
};

const SEV_TONE: Record<Severity, { icon: typeof Info; classes: string }> = {
  baixa: { icon: Info, classes: "bg-slate-50 border-slate-200 text-slate-700" },
  media: {
    icon: AlertTriangle,
    classes: "bg-amber-50 border-amber-200 text-amber-800",
  },
  alta: {
    icon: ShieldAlert,
    classes: "bg-red-50 border-red-200 text-red-800",
  },
};

export function InsightsPanel({ insights }: Props) {
  const c = CLASSIF_TONE[insights.classificacao];

  return (
    <div className="flex h-full flex-col rounded-[24px] border border-black/5 bg-white/80 p-6 shadow-apple backdrop-blur-xl">
      <div className="mb-5 flex items-center gap-3">
        <Sparkles className="h-5 w-5 text-brand" />
        <h3 className="text-lg font-semibold tracking-tight text-[#1d1d1f]">Insights IA</h3>
        <span
          className={clsx(
            "ml-2 inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-tight shadow-sm",
            c.badge,
          )}
        >
          {c.label}
        </span>
      </div>

      <p className="mb-5 text-[13px] font-medium leading-relaxed tracking-tight text-black/70">{insights.resumo}</p>

      <div className="flex-1 space-y-2.5 overflow-y-auto pr-1 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:'none'] [scrollbar-width:'none']">
        {insights.alertas.map((a, idx) => {
          const t = SEV_TONE[a.severidade];
          const Icon = t.icon;
          return (
            <div
              key={idx}
              className={clsx("flex items-start gap-3 rounded-[16px] border p-3.5 text-[12px] shadow-sm", t.classes)}
            >
              <Icon className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p className="font-semibold tracking-tight">{a.titulo}</p>
                <p className="mt-1 text-[11px] font-medium opacity-80 leading-snug">{a.descricao}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
