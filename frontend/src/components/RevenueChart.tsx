"use client";

import { useEffect, useRef, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatBRL } from "@/lib/api";
import type { TimeseriesPoint } from "@/lib/types";

interface Props {
  data: TimeseriesPoint[];
}

const CHART_HEIGHT = 350;

export function RevenueChart({ data }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;
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

  const hasData = Array.isArray(data) && data.length > 0;

  return (
    <div className="flex h-full flex-col rounded-[24px] border border-black/5 bg-white/80 p-6 shadow-apple backdrop-blur-xl transition-all duration-300 hover:shadow-apple-hover">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold tracking-tight text-[#1d1d1f]">Evolução temporal</h3>
          <p className="mt-0.5 text-xs font-medium tracking-tight text-black/50">
            Receita mensal (transações pagas){hasData ? ` · ${data.length} meses` : ""}
          </p>
        </div>
      </div>

      <div ref={containerRef} className="w-full" style={{ height: CHART_HEIGHT, minWidth: 0, minHeight: 0 }}>
        {!hasData && (
          <div className="flex h-full w-full items-center justify-center text-xs text-black/40">
            Sem dados para exibir.
          </div>
        )}
        {hasData && width > 0 && (
          <LineChart
            width={width}
            height={CHART_HEIGHT}
            data={data}
            margin={{ top: 5, right: 20, left: 0, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" strokeWidth={1} vertical={false} />
            <XAxis
              dataKey="periodo"
              stroke="#94a3b8"
              fontSize={13}
              fontWeight={500}
              tickMargin={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={13}
              fontWeight={500}
              tickLine={false}
              axisLine={false}
              tickMargin={12}
              tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v.toString())}
            />
            <Tooltip
              formatter={(v) => [<span className="font-semibold text-brand" key="val">{formatBRL(Number(v))}</span>, <span className="font-medium text-black/50" key="lbl">Receita</span>]}
              labelClassName="mb-1 text-[11px] font-medium tracking-wide uppercase text-black/40"
              itemStyle={{ margin: 0, padding: 0 }}
              contentStyle={{
                borderRadius: "16px",
                border: "1px solid rgba(0,0,0,0.05)",
                boxShadow: "0 8px 32px rgba(0,0,0,0.08)",
                background: "rgba(255,255,255,0.85)",
                backdropFilter: "blur(20px)",
                WebkitBackdropFilter: "blur(20px)",
                padding: "8px 12px",
              }}
            />
            <Line
              type="monotone"
              dataKey="receita"
              stroke="#4A00E0"
              strokeWidth={3}
              dot={{ r: 4, fill: "#4A00E0", strokeWidth: 2, stroke: "#fff" }}
              activeDot={{ r: 6, fill: "#4A00E0", strokeWidth: 2, stroke: "#fff" }}
              animationDuration={1500}
              animationEasing="ease-out"
            />
          </LineChart>
        )}
      </div>
    </div>
  );
}
