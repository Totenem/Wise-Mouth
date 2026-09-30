"use client";
import { useEffect, useState } from "react";

export type Theme = "dark" | "light";
const KEY = "wm-theme";
const EVENT = "wm-theme-change";

export function currentTheme(): Theme {
  return typeof document !== "undefined" && document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

export function setTheme(t: Theme) {
  document.documentElement.dataset.theme = t;
  try {
    localStorage.setItem(KEY, t);
  } catch {}
  window.dispatchEvent(new Event(EVENT));
}

export function useTheme(): Theme {
  const [theme, setT] = useState<Theme>("dark");
  useEffect(() => {
    const sync = () => setT(currentTheme());
    sync();
    window.addEventListener(EVENT, sync);
    return () => window.removeEventListener(EVENT, sync);
  }, []);
  return theme;
}

// Runs before first paint (see layout.tsx) so there's no dark->light flash.
export const THEME_INIT_SCRIPT = `try{var t=localStorage.getItem("${KEY}");if(t!=="light"&&t!=="dark"){t=matchMedia("(prefers-color-scheme: light)").matches?"light":"dark"}document.documentElement.dataset.theme=t}catch(e){document.documentElement.dataset.theme="dark"}`;
