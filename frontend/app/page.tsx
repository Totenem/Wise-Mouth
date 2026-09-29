"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Mic, History } from "lucide-react";

function randomRoom() {
  return Math.random().toString(16).slice(2, 10);
}

export default function Landing() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [code, setCode] = useState("");

  useEffect(() => {
    try {
      setName(localStorage.getItem("wm-name") ?? "");
    } catch {}
  }, []);

  const go = (room: string) => {
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
          onClick={() => go(randomRoom())}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-500 px-4 py-3 font-semibold text-ink-950 hover:bg-emerald-400"
        >
          <Mic size={18} /> Start Conversation
        </button>
        <div className="flex gap-2">
          <input
            value={code}
            onChange={(e) => setCode(e.target.value.trim())}
            placeholder="Room code to join"
            className="min-w-0 flex-1 rounded-lg border border-ink-600 bg-ink-800 px-4 py-2.5 outline-none focus:border-emerald-400"
          />
          <button
            disabled={!code}
            onClick={() => go(code)}
            className="rounded-lg border border-ink-600 px-4 py-2.5 hover:bg-ink-700 disabled:opacity-40"
          >
            Join
          </button>
        </div>
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
