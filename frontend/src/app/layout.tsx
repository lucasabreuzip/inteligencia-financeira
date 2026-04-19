import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Inteligência Financeira",
  description: "Análise inteligente de dados financeiros",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="bg-slate-50 text-slate-900 antialiased">{children}</body>
    </html>
  );
}
