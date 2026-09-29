"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Mic, History, LogOut } from "lucide-react";
import { clearSession, getToken, getUsername } from "@/lib/api";
import { BusyLabel, FullPageLoader } from "@/components/Loading";

function randomRoom() {
  return Math.random().toString(16).slice(2, 10);
}

export default function Landing() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [user, setUser] = useState<string | null>(null);
  const [busy, setBusy] = useState<"start" | "join" | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setUser(getUsername());
    try {
      setName(localStorage.getItem("wm-name") ?? getUsername() ?? "");
    } catch {}
  }, [router]);

  const logout = () => {
    clearSession();
    router.replace("/login");
  };

  if (!user) return <FullPageLoader messages={["Checking your session...", "Almost ready..."]} />;

  const go = (room: string, kind: "start" | "join") => {
    if (busy) return;
    setBusy(kind);
    const n = name.trim() || "Guest";
    try {
      localStorage.setItem("wm-name", n);
    } catch {}
    router.push(`/meeting/${room}?name=${encodeURIComponent(n)}`);
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center px-6 text-center">
      <div className="mb-3 text-xs font-semibold uppercase tracking-[0.4em] text-emerald-400">WiseMouth</div>
      <h1 className="text-4xl font-bold leading-tight sm:text-5xl">
        See what the conversation
        <br />
        doesn&apos;t explicitly say.
      </h1>
      <p className="mt-4 max-w-lg text-slate-400">
        A real-time intelligence layer for online conversations. It surfaces observable signals such as uncertainty,
        commitments, changed commitments, repeated concerns and unanswered questions, each with its evidence.
      </p>

      <div className="mt-8 w-full max-w-sm space-y-3">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Your name (e.g. John)"
          className="w-full rounded-lg border border-ink-600 bg-ink-800 px-4 py-2.5 outline-none focus:border-emerald-400"
        />
        <button
          onClick={() => go(randomRoom(), "start")}
          disabled={!!busy}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-500 px-4 py-3 font-semibold text-ink-950 hover:bg-emerald-400 disabled:opacity-60"
        >
          <BusyLabel busy={busy === "start"} busyText="Creating your room...">
            <Mic size={18} /> Start Conversation
          </BusyLabel>
        </button>
        <div className="flex gap-2">
          <input
            value={code}
            onChange={(e) => setCode(e.target.value.trim())}
            placeholder="Room code to join"
            className="min-w-0 flex-1 rounded-lg border border-ink-600 bg-ink-800 px-4 py-2.5 outline-none focus:border-emerald-400"
          />
          <button
            disabled={!code || !!busy}
            onClick={() => go(code, "join")}
            className="flex items-center gap-2 rounded-lg border border-ink-600 px-4 py-2.5 hover:bg-ink-700 disabled:opacity-40"
          >
            <BusyLabel busy={busy === "join"} busyText="Joining...">
              Join
            </BusyLabel>
          </button>
        </div>
        <button onClick={logout} className="flex w-full items-center justify-center gap-2 text-sm text-slate-400 hover:text-white">
          <LogOut size={14} /> Log out ({user})
        </button>
        <Link href="/history" className="flex items-center justify-center gap-2 pt-2 text-sm text-slate-400 hover:text-white">
          <History size={14} /> Past conversations
        </Link>
      </div>

      <p className="mt-10 text-xs text-slate-500">
        WiseMouth analyses observable language. It does not detect emotions, lies or intent.
      </p>
    </main>
  );
}
