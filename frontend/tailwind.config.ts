import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "rgb(var(--ink-950) / <alpha-value>)",
          900: "rgb(var(--ink-900) / <alpha-value>)",
          800: "rgb(var(--ink-800) / <alpha-value>)",
          700: "rgb(var(--ink-700) / <alpha-value>)",
          600: "rgb(var(--ink-600) / <alpha-value>)",
        },
        // text greys flip with the theme so they stay readable in light mode
        slate: {
          100: "rgb(var(--fg-100) / <alpha-value>)",
          200: "rgb(var(--fg-200) / <alpha-value>)",
          300: "rgb(var(--fg-300) / <alpha-value>)",
          400: "rgb(var(--fg-400) / <alpha-value>)",
          500: "rgb(var(--fg-500) / <alpha-value>)",
          950: "#020617",
        },
      },
      keyframes: {
        pop: { "0%": { transform: "scale(0.9)", opacity: "0" }, "100%": { transform: "scale(1)", opacity: "1" } },
        slidein: { "0%": { transform: "translateY(8px)", opacity: "0" }, "100%": { transform: "translateY(0)", opacity: "1" } },
      },
      animation: { pop: "pop .25s ease-out", slidein: "slidein .3s ease-out" },
    },
  },
  plugins: [],
};
export default config;
