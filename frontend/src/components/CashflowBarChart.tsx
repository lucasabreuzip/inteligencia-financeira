"use client";

import { useEffect, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Point {
  mes: string;
  variacao_mm: number;
  receita: number;
}

interface Props {
  data: Point[];
  height?: number;
}

const POSITIVE = "#10b981";
const NEGATIVE = "#ef4444";
const NEUTRAL = "#94a3b8";

export function CashflowBarChart({ data, height = 180 }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    if (!ref.current) return;
    const el = ref.current;
    const update = () => setWidth(el.clientWidth);
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    window.addEventListener("resize", update);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", update);
    };
  }, []);

  if (!data || data.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center text-xs text-black/40">
        Dados insuficientes.
      </div>
    );
  }

  const chartData = data.map((p) => ({
    ...p,
    pct: +(p.variacao_mm * 100).toFixed(1),
  }));

  return (
    <div ref={ref} className="w-full" style={{ height, minWidth: 0 }}>
      {width > 0 && (
        <BarChart
          width={width}
          height={height}
          data={chartData}
          margin={{ top: 4, right: 8, left: 0, bottom: 4 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="mes"
            stroke="#94a3b8"
            fontSize={10}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            stroke="#94a3b8"
            fontSize={10}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v}%`}
          />
          <ReferenceLine y={0} stroke="#cbd5e1" strokeWidth={1} />
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.03)" }}
            contentStyle={{
              borderRadius: 12,
              border: "1px solid rgba(0,0,0,0.06)",
              background: "rgba(255,255,255,0.95)",
              backdropFilter: "blur(12px)",
              padding: "8px 12px",
              fontSize: 12,
            }}
            formatter={(value) => [`${Number(value).toFixed(1)}%`, "Variação M/M"]}
            labelFormatter={(label) => `Mês ${label}`}
          />
          <Bar dataKey="pct" radius={[4, 4, 0, 0]}>
            {chartData.map((p, idx) => (
              <Cell
                key={idx}
                fill={p.pct > 0 ? POSITIVE : p.pct < 0 ? NEGATIVE : NEUTRAL}
              />
            ))}
          </Bar>
        </BarChart>
      )}
    </div>
  );
}
