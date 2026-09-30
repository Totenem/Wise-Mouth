"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, EyeOff, Link2, MessageCircleQuestion, Quote } from "lucide-react";
import { getToken } from "@/lib/api";
import { SIGNAL_META, SIGNAL_ORDER } from "@/lib/signals";
import type { SignalType } from "@/lib/types";

// A tiny scripted excerpt of the built-in demo, replayed as a looping animation.
const EXCERPT: { speaker: string; text: string; signal?: SignalType }[] = [
  { speaker: "John", text: "Okay, for the release, I'll handle the deployment.", signal: "commitment" },
  { speaker: "Sarah", text: "Yeah, I guess that could work for the timeline.", signal: "hedging" },
  { speaker: "Maria", text: "The authentication service is still my biggest concern.", signal: "repeated_concern" },
  { speaker: "John", text: "Actually, I don't think I'll have enough time to handle the deployment.", signal: "commitment_change" },
  { speaker: "Sarah", text: "Who's going to handle the migration?" },
  { speaker: "Michael", text: "The frontend demo looks good so far.", signal: "unanswered_question" },
];

const PROBLEMS = [
  {
    icon: EyeOff,
    title: "Agreement that isn't",
    body: "\"Yeah, I guess that works.\" It gets logged as a yes. WiseMouth flags the hedge.",
  },
  {
    icon: Link2,
    title: "Commitments that quietly change",
    body: "Someone takes an action, then backs out ten minutes later. We connect the two moments.",
  },
  {
    icon: MessageCircleQuestion,
    title: "Questions nobody answers",
    body: "The conversation moves on. The question stays open until someone notices. Now it's flagged.",
  },
];

function LiveExcerpt() {
  const [shown, setShown] = useState(1);

  useEffect(() => {
    const t = setInterval(() => setShown((n) => (n >= EXCERPT.length + 2 ? 1 : n + 1)), 1800);
    return () => clearInterval(t);
  }, []);

  const visible = EXCERPT.slice(0, Math.min(shown, EXCERPT.length));
  return (
    <div className="w-full max-w-xl rounded-2xl border border-ink-600 bg-ink-900/80 p-5 text-left shadow-2xl shadow-emerald-500/5">
      <div className="mb-4 flex items-center gap-2 text-xs uppercase tracking-widest text-slate-500">
        <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" /> Live conversation
      </div>
      <ul className="space-y-3">
        {visible.map((l, i) => (
          <li key={`${i}-${l.text}`} className="animate-slidein">
            <div className="text-xs font-semibold text-slate-400">{l.speaker}</div>
            <p className="text-sm text-slate-200 sm:text-base">{l.text}</p>
            {l.signal && (
              <span
                className={`mt-1.5 inline-block animate-pop rounded-full border px-2.5 py-0.5 text-[11px] font-semibold tracking-wide ${SIGNAL_META[l.signal].chip}`}
              >
                {SIGNAL_META[l.signal].label}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Landing() {
  const [authed, setAuthed] = useState(false);
  useEffect(() => setAuthed(!!getToken()), []);
  const cta = authed ? "/start" : "/login";

  return (
    <main className="overflow-x-hidden">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <span className="text-xs font-semibold uppercase tracking-[0.4em] text-emerald-400">WiseMouth</span>
        <Link href={cta} className="text-sm text-slate-300 hover:text-slate-100">
          {authed ? "Open app" : "Log in"}
        </Link>
      </nav>

      {/* Hero */}
      <section className="mx-auto flex max-w-3xl flex-col items-center px-6 pb-16 pt-14 text-center sm:pt-24">
        <p className="max-w-xl text-lg text-slate-400">
          A transcript tells you what people said. It doesn&apos;t tell you what&apos;s actually happening in the conversation.
        </p>
        <h1 className="mt-6 text-4xl font-bold leading-tight sm:text-6xl">
          See what the conversation
          <br />
          <span className="bg-gradient-to-r from-emerald-300 to-sky-400 bg-clip-text text-transparent">
            doesn&apos;t explicitly say.
          </span>
        </h1>
        <p className="mt-6 max-w-xl text-slate-400">
          These moments get lost. WiseMouth makes them visible, in real time, with the evidence behind every signal.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link
            href={cta}
            className="flex items-center gap-2 rounded-lg bg-emerald-500 px-6 py-3 font-semibold text-slate-950 hover:bg-emerald-400"
          >
            {authed ? "Start a conversation" : "Get started"} <ArrowRight size={18} />
          </Link>
          <a href="#how" className="rounded-lg border border-ink-600 px-6 py-3 hover:bg-ink-700">
            See how it works
          </a>
        </div>
      </section>

      {/* Animated example */}
      <section className="flex justify-center px-6 pb-24">
        <LiveExcerpt />
      </section>

      {/* Problem */}
      <section className="mx-auto max-w-6xl px-6 pb-24">
        <h2 className="mb-10 text-center text-2xl font-bold sm:text-3xl">Important things hide in how a conversation moves</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {PROBLEMS.map(({ icon: Icon, title, body }) => (
            <div key={title} className="rounded-xl border border-ink-600 bg-ink-800 p-6">
              <Icon className="mb-4 text-emerald-400" size={24} />
              <h3 className="mb-2 font-semibold">{title}</h3>
              <p className="text-sm text-slate-400">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Signals */}
      <section id="how" className="mx-auto max-w-4xl scroll-mt-8 px-6 pb-24 text-center">
        <h2 className="text-2xl font-bold sm:text-3xl">Seven observable signals</h2>
        <p className="mx-auto mt-3 max-w-xl text-slate-400">
          AssemblyAI hears it. Rules detect it. The LLM understands it. Conversation state connects it. WiseMouth makes it
          visible.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-2.5">
          {SIGNAL_ORDER.map((t) => (
            <span key={t} className={`rounded-full border px-4 py-1.5 text-xs font-semibold tracking-wide ${SIGNAL_META[t].chip}`}>
              {SIGNAL_META[t].label}
            </span>
          ))}
        </div>
      </section>

      {/* Trust */}
      <section className="mx-auto max-w-3xl px-6 pb-24">
        <div className="rounded-2xl border border-ink-600 bg-ink-800 p-8 text-center">
          <Quote className="mx-auto mb-3 text-emerald-400" size={22} />
          <p className="text-lg font-semibold">Evidence first, never mind-reading.</p>
          <p className="mt-2 text-sm text-slate-400">
            Every signal shows the exact words, the timestamp and the earlier statement it connects to. WiseMouth analyses
            observable language. It does not detect emotions, lies or intent.
          </p>
        </div>
      </section>

      {/* Closing CTA */}
      <section className="px-6 pb-24 text-center">
        <p className="text-xl font-semibold sm:text-2xl">
          We&apos;re not just recording conversations.
          <br />
          We&apos;re understanding how they evolve.
        </p>
        <Link
          href={cta}
          className="mt-8 inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-6 py-3 font-semibold text-slate-950 hover:bg-emerald-400"
        >
          {authed ? "Start a conversation" : "Try the demo"} <ArrowRight size={18} />
        </Link>
      </section>

      <footer className="border-t border-ink-700 py-6 text-center text-xs text-slate-500">
        WiseMouth · See what the conversation doesn&apos;t explicitly say.
      </footer>
    </main>
  );
}
