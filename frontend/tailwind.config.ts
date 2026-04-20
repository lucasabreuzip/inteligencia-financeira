import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Tema roxo profundo
        brand: { DEFAULT: "#4A00E0", dark: "#3A00B0", light: "#EAE2F8" },
      },
      boxShadow: {
        'apple': '0 4px 24px rgba(0,0,0,0.04)',
        'apple-hover': '0 8px 32px rgba(0,0,0,0.08)',
        'apple-float': '0 20px 40px rgba(0,0,0,0.08)',
      },
      borderRadius: {
        '2.5xl': '1.25rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [
    typography,
  ],
};

export default config;
