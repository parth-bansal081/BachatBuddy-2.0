import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

// PLACEHOLDER palette so the ported (shadcn) components are readable in Phase 0.
// The real design tokens replace this in the UI phase.
const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#ffffff",
        foreground: "#111111",
        primary: { DEFAULT: "#111111", foreground: "#ffffff" },
        secondary: { DEFAULT: "#f1f1f1", foreground: "#111111" },
        muted: { DEFAULT: "#f1f1f1", foreground: "#6b7280" },
        accent: { DEFAULT: "#f1f1f1", foreground: "#111111" },
        destructive: { DEFAULT: "#dc2626", foreground: "#ffffff" },
        popover: { DEFAULT: "#ffffff", foreground: "#111111" },
        card: { DEFAULT: "#ffffff", foreground: "#111111" },
        border: "#e5e7eb",
        input: "#e5e7eb",
        ring: "#111111",
      },
      borderRadius: { lg: "0.5rem", md: "0.375rem", sm: "0.25rem" },
    },
  },
  plugins: [animate],
};

export default config;
