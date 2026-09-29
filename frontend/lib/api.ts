// Trailing slash stripped so `${API_URL}/path` never becomes `//path` (which breaks routing/CORS preflight).
export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");
export const WS_URL = API_URL.replace(/^http/, "ws");

const TOKEN_KEY = "wm-token";
const USER_KEY = "wm-user";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getUsername(): string | null {
  try {
    return localStorage.getItem(USER_KEY);
  } catch {
    return null;
  }
}

export function setSession(token: string, username: string) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, username);
  } catch {}
}

export function clearSession() {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {}
}

export class HttpError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const r = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    ...init,
    headers: { ...(init.headers ?? {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  });
  if (r.status === 401 && token) clearSession(); // expired/invalid token
  if (!r.ok) {
    const detail = await r.json().then((d) => d.detail).catch(() => null);
    throw new HttpError(r.status, typeof detail === "string" ? detail : `${path}: ${r.status}`);
  }
  return r.json();
}

export const getJSON = <T,>(path: string) => request<T>(path);

export const postJSON = <T,>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
