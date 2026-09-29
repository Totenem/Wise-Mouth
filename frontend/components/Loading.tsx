"use client";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

export function Spinner({ size = 16, className = "" }: { size?: number; className?: string }) {
  return <Loader2 size={size} aria-hidden className={`animate-spin motion-reduce:animate-none ${className}`} />;
}

/** Grey placeholder block; size it with className (e.g. "h-4 w-32"). */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden className={`animate-pulse rounded-md bg-ink-700 motion-reduce:animate-none ${className}`} />;
}

/** Cycles through messages so long waits (cold backend, slow network) feel alive. */
export function RotatingMessage({ messages, intervalMs = 2200 }: { messages: string[]; intervalMs?: number }) {
  const [i, setI] = useState(0);
  useEffect(() => {
    if (messages.length < 2) return;
    // Stop on the last message instead of looping back to the first.
    const t = setInterval(() => setI((n) => Math.min(n + 1, messages.length - 1)), intervalMs);
    return () => clearInterval(t);
  }, [messages.length, intervalMs]);
  return (
    <span key={i} className="animate-slidein">
      {messages[i]}
    </span>
  );
}

/** Spinner + rotating status line, announced to screen readers. */
export function StatusLine({ messages, className = "" }: { messages: string[]; className?: string }) {
  return (
    <div role="status" aria-live="polite" className={`flex items-center gap-2 text-sm text-slate-400 ${className}`}>
      <Spinner className="text-emerald-400" />
      <RotatingMessage messages={messages} />
    </div>
  );
}

export function FullPageLoader({ messages }: { messages: string[] }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <div className="text-xs font-semibold uppercase tracking-[0.4em] text-emerald-400">WiseMouth</div>
      <StatusLine messages={messages} />
    </main>
  );
}

/** Button label that swaps to a spinner while busy. */
export function BusyLabel({ busy, busyText, children }: { busy: boolean; busyText: string; children: React.ReactNode }) {
  return busy ? (
    <>
      <Spinner /> {busyText}
    </>
  ) : (
    <>{children}</>
  );
}
