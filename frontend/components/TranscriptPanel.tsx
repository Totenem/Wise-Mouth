"use client";
import { useEffect, useRef } from "react";
import { fmtTs } from "@/lib/signals";
import { Segment, Signal } from "@/lib/types";
import { SignalChip } from "./SignalChip";

export function TranscriptPanel({
  transcript,
  partials,
  signals,
  live,
  onOpen,
}: {
  transcript: Segment[];
  partials: Record<string, string>;
  signals: Signal[];
  live: boolean;
  onOpen: (s: Signal) => void;
}) {
  const end = useRef<HTMLDivElement>(null);
  const partialCount = Object.keys(partials).length;
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [transcript.length, partialCount]);

  // A signal belongs to the segment it came from (same speaker + timestamp).
  const forSegment = (seg: Segment) => signals.filter((s) => s.speaker === seg.speaker && s.timestamp_ms === seg.start_ms);

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Live Transcript</h2>
        {live && (
          <span className="flex items-center gap-1.5 text-xs text-red-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-red-500" />
            LIVE
          </span>
        )}
      </div>
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto pr-2">
        {transcript.length === 0 && partialCount === 0 && (
          <p className="text-sm text-slate-500">
            Nothing said yet. Turn on your mic, type a line, or run the demo conversation.
          </p>
        )}
        {transcript.map((t) => (
          <div key={t.id} className="animate-slidein">
            <div className="text-xs text-slate-500">
              <span className="font-semibold text-slate-300">{t.speaker}</span> · {fmtTs(t.start_ms)}
            </div>
            <p className="text-slate-100">{t.text}</p>
            <div className="mt-1 flex flex-wrap gap-1">
              {forSegment(t).map((s) => (
                <SignalChip key={s.id} type={s.type} count={s.count} onClick={() => onOpen(s)} />
              ))}
            </div>
          </div>
        ))}
        {Object.entries(partials).map(([sp, text]) => (
          <div key={sp} className="opacity-60">
            <div className="text-xs text-slate-500">
              <span className="font-semibold text-slate-300">{sp}</span> · speaking...
            </div>
            <p className="text-slate-300">{text}</p>
          </div>
        ))}
        <div ref={end} />
      </div>
    </div>
  );
}
