"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { postJSON, setSession } from "@/lib/api";
import { BusyLabel } from "@/components/Loading";

interface Session {
  token: string;
  user: { id: string; username: string };
}

export default function Login() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const s = await postJSON<Session>(`/api/auth/${mode}`, { username, password });
      setSession(s.token, s.user.username);
      router.replace("/start");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reach the backend.");
    } finally {
      setBusy(false);
    }
  };

  const input = "w-full rounded-lg border border-ink-600 bg-ink-800 px-4 py-2.5 outline-none focus:border-emerald-400";
  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col items-center justify-center px-6">
      <div className="mb-6 text-xs font-semibold uppercase tracking-[0.4em] text-emerald-400">WiseMouth</div>
      <form onSubmit={submit} className="w-full space-y-3">
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          autoComplete="username"
          className={input}
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password (8+ characters)"
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          className={input}
        />
        {error && <p className="text-sm text-red-300">{error}</p>}
        <button
          disabled={busy || !username || !password}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-500 px-4 py-3 font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-40"
        >
          <BusyLabel busy={busy} busyText={mode === "login" ? "Signing you in..." : "Creating your account..."}>
            {mode === "login" ? "Log in" : "Create account"}
          </BusyLabel>
        </button>
      </form>
      <button
        onClick={() => {
          setMode(mode === "login" ? "register" : "login");
          setError("");
        }}
        className="mt-4 text-sm text-slate-400 hover:text-slate-100"
      >
        {mode === "login" ? "No account? Create one" : "Have an account? Log in"}
      </button>
    </main>
  );
}
