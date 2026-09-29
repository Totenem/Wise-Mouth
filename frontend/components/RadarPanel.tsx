"use client";
import { useEffect, useRef, useState } from "react";
import { SIGNAL_META, SIGNAL_ORDER, countSignals, fmtTs } from "@/lib/signals";
import { Signal } from "@/lib/types";
import { SignalChip } from "./SignalChip";

function Counter({ value }: { value: number }) {
  const [bump, setBump] = useState(false);
  const prev = useRef(value);
  useEffect(() => {
    if (prev.current !== value) {
      prev.current = value;
      setBump(true);
      const t = setTimeout(() => setBump(false), 300);
      return () => clearTimeout(t);
    }
  }, [value]);
  return (
    <span className={`text-lg font-semibold tabular-nums transition-transform ${bump ? "scale-125" : ""}`}>{value}</span>
  );
}

export function LiveSignalCard({ signal, onOpen }: { signal: Signal | null; onOpen: (s: Signal) => void }) {
  if (!signal) {
    return (
      <div className="rounded-xl border border-dashed border-ink-600 p-4 text-sm text-slate-400">
        Listening. Signals appear here with the evidence behind them.
      </div>
    );
  }
  const m = SIGNAL_META[signal.type];
  return (
    <div
      key={signal.id + signal.count}
      onClick={() => onOpen(signal)}
      className="animate-pop cursor-pointer rounded-xl border bg-ink-800 p-4"
      style={{ borderColor: m.color + "66" }}
    >
      <div className="mb-2 flex items-center justify-between">
        <SignalChip type={signal.type} count={signal.count} />
        <span className="text-xs text-slate-400">{fmtTs(signal.timestamp_ms)}</span>
      </div>
      <p className="mb-3 text-sm text-slate-300">{signal.summary}</p>
      {signal.related && (
        <div className="mb-2 rounded-lg bg-ink-900 p-2 text-sm">
          <div className="text-[10px] uppercase tracking-wider text-slate-500">
            Earlier · {fmtTs(signal.related.timestamp_ms)}
          </div>
          <div className="italic text-slate-300">&ldquo;{signal.related.text}&rdquo;</div>
        </div>
      )}
      <div className="rounded-lg bg-ink-900 p-2 text-sm">
        <div className="text-[10px] uppercase tracking-wider text-slate-500">
          {signal.related ? "Now" : "Evidence"} · {signal.speaker}
        </div>
        <div className="italic text-slate-100">&ldquo;{signal.evidence}&rdquo;</div>
      </div>
    </div>
  );
}

export function RadarPanel({
  signals,
  latest,
  onOpen,
}: {
  signals: Record<string, Signal>;
  latest: Signal | null;
  onOpen: (s: Signal) => void;
}) {
  const counts = countSignals(Object.values(signals));
  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto">
      <div>
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Conversation Radar</h2>
        <div className="grid grid-cols-1 gap-1.5">
          {SIGNAL_ORDER.map((t) => (
            <div key={t} className="flex items-center justify-between rounded-lg bg-ink-800 px-3 py-1.5">
              <span className="flex items-center gap-2 text-sm text-slate-300">
                <span className={`h-2.5 w-2.5 rounded-full ${SIGNAL_META[t].dot}`} />
                {SIGNAL_META[t].radar}
              </span>
              <Counter value={counts[t]} />
            </div>
          ))}
        </div>
      </div>
      <div>
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Live Signal</h2>
        <LiveSignalCard signal={latest} onOpen={onOpen} />
      </div>
    </div>
  );
}
