"use client";

import { useRef, useState } from "react";
import { Upload, Loader2, FileSpreadsheet } from "lucide-react";

import { uploadCsv } from "@/lib/api";
import type { JobCreatedResponse } from "@/lib/types";

interface Props {
  onJobCreated: (job: JobCreatedResponse) => void;
  disabled?: boolean;
}

const ACCEPTED_EXT = [".csv", ".xlsx", ".xls"];

function isAccepted(file: File): boolean {
  const name = file.name.toLowerCase();
  return ACCEPTED_EXT.some((ext) => name.endsWith(ext));
}

export function UploadCard({ onJobCreated, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  async function handleFile(file: File) {
    if (!isAccepted(file)) {
      setError("Formato não suportado. Use .csv, .xlsx ou .xls.");
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const job = await uploadCsv(file);
      onJobCreated(job);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha no upload.");
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  const interactionDisabled = busy || !!disabled;

  return (
    <div className="rounded-[24px] border border-black/5 bg-white/80 p-6 shadow-apple backdrop-blur-xl transition-all duration-300 hover:shadow-apple-hover">
      <div className="mb-4 flex items-start gap-3">
        <div className="rounded-xl bg-brand/10 p-2.5 text-brand">
          <FileSpreadsheet className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <h2 className="text-lg font-semibold tracking-tight text-[#1d1d1f]">
            Enviar arquivo de transações
          </h2>
          <p className="mt-0.5 text-xs font-medium tracking-tight text-black/50">
            CSV, XLSX ou XLS · Máx. 25MB
          </p>
        </div>
      </div>

      <div
        onDragOver={(e) => {
          if (interactionDisabled) return;
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (interactionDisabled) return;
          const f = e.dataTransfer.files?.[0];
          if (f) handleFile(f);
        }}
        onClick={() => !interactionDisabled && inputRef.current?.click()}
        className={`group relative flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-6 py-6 text-center transition-all ${interactionDisabled
          ? "cursor-not-allowed border-black/10 bg-black/[0.02] opacity-60"
          : dragOver
            ? "border-brand bg-brand/5"
            : "border-black/10 bg-black/[0.015] hover:border-brand/40 hover:bg-brand/[0.03]"
          }`}
      >
        <div
          className={`rounded-full bg-brand/10 p-3 text-brand shadow-sm transition-transform ${!interactionDisabled ? "group-hover:scale-110" : ""
            }`}
        >
          {busy ? <Loader2 className="h-5 w-5 animate-spin" /> : <Upload className="h-5 w-5" />}
        </div>

        <div>
          <p className="text-sm font-semibold tracking-tight text-[#1d1d1f]">
            {busy ? "Enviando arquivo…" : "Arraste o arquivo ou clique para selecionar"}
          </p>
          <p className="mt-0.5 text-[11px] font-medium tracking-tight text-black/45">
            .csv · .xlsx · .xls
          </p>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
      </div>

      <details className="mt-3 text-xs">
        <summary className="cursor-pointer select-none font-medium tracking-tight text-black/50 hover:text-black/70">
          Colunas esperadas
        </summary>
        <div className="mt-2 rounded-lg border border-black/5 bg-black/[0.02] px-3 py-2">
          <code className="text-[11px] tracking-tight text-black/70">
            id; valor; data; status; cliente; descricao
          </code>
          <p className="mt-1 text-[11px] text-black/45">
            status aceita: pago · pendente · atrasado · cancelado
          </p>
        </div>
      </details>

      {error && (
        <div className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700 shadow-sm">
          {error}
        </div>
      )}
    </div>
  );
}
