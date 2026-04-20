import { clsx } from "clsx";
import type { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string;
  hint?: string;
  icon?: LucideIcon;
  tone?: "default" | "success" | "warning" | "danger";
}

const TONE: Record<NonNullable<Props["tone"]>, string> = {
  default: "bg-brand/10 text-brand",
  success: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-700",
  danger: "bg-red-100 text-red-700",
};

export function KpiCard({ title, value, hint, icon: Icon, tone = "default" }: Props) {
  return (
    <div className="rounded-[24px] border border-black/5 bg-white/80 p-6 shadow-apple backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold tracking-tight text-black/50">{title}</p>
        {Icon && (
          <span className={clsx("rounded-full p-2.5", TONE[tone])}>
            <Icon className="h-4 w-4" />
          </span>
        )}
      </div>
      <p className="mt-4 text-3xl font-semibold tracking-tight tabular-nums text-[#1d1d1f]">{value}</p>
      {hint && <p className="mt-1 text-xs font-medium tracking-tight text-black/40">{hint}</p>}
    </div>
  );
}
