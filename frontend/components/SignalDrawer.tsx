"use client";
import { X } from "lucide-react";
import { SIGNAL_META, confidenceLabel, fmtTs } from "@/lib/signals";
import { Signal } from "@/lib/types";
import { SignalChip } from "./SignalChip";

type Mention = { speaker: string; text: string; timestamp_ms: number };

export function SignalDrawer({ signal, onClose }: { signal: Signal | null; onClose: () => void }) {
  if (!signal) return null;
  const mentions = (signal.meta.mentions as Mention[] | undefined) ?? [];
  const showStatus = signal.type === "disagreement" || signal.type === "unanswered_question";
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={onClose}>
      <aside
        onClick={(e) => e.stopPropagation()}
        className="h-full w-full max-w-md animate-slidein overflow-y-auto border-l border-ink-600 bg-ink-900 p-6"
      >
        <div className="mb-4 flex items-center justify-between">
          <SignalChip type={signal.type} count={signal.count} />
          <button onClick={onClose} aria-label="Close" className="text-slate-400 hover:text-white">
            <X size={18} />
          </button>
        </div>
        <p className="mb-4 text-slate-200">{signal.summary}</p>
        <dl className="mb-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-slate-500">Speaker</dt>
            <dd>{signal.speaker}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Timestamp</dt>
            <dd>{fmtTs(signal.timestamp_ms)}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Confidence</dt>
            <dd>
              {confidenceLabel(signal.confidence)} ({signal.confidence.toFixed(2)})
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Topic</dt>
            <dd>{signal.topic ?? "-"}</dd>
          </div>
          {signal.participants.length > 0 && (
            <div className="col-span-2">
              <dt className="text-slate-500">Participants</dt>
              <dd>{signal.participants.join(", ")}</dd>
            </div>
          )}
          {showStatus && (
            <div className="col-span-2">
              <dt className="text-slate-500">Status</dt>
              <dd>
                {signal.status === "resolved"
                  ? "Resolved"
                  : ((signal.meta.status_text as string) ?? "No response detected")}
              </dd>
            </div>
          )}
        </dl>
        {signal.related && (
          <section className="mb-3">
            <h3 className="mb-1 text-xs uppercase tracking-wider text-slate-500">
              Earlier · {fmtTs(signal.related.timestamp_ms)} · {signal.related.speaker}
            </h3>
            <blockquote className="rounded-lg bg-ink-800 p-3 italic text-slate-300">
              &ldquo;{signal.related.text}&rdquo;
            </blockquote>
          </section>
        )}
        <section className="mb-3">
          <h3 className="mb-1 text-xs uppercase tracking-wider text-slate-500">
            {signal.related ? "Later" : "Evidence"} · {fmtTs(signal.timestamp_ms)} · {signal.speaker}
          </h3>
          <blockquote
            className="rounded-lg border-l-2 bg-ink-800 p-3 italic text-slate-100"
            style={{ borderColor: SIGNAL_META[signal.type].color }}
          >
            &ldquo;{signal.evidence}&rdquo;
          </blockquote>
        </section>
        {typeof signal.meta.pattern === "string" && (
          <p className="mb-3 text-sm text-slate-400">
            Detected pattern: <span className="text-slate-200">{signal.meta.pattern}</span>
          </p>
        )}
        {mentions.length > 0 && (
          <section>
            <h3 className="mb-1 text-xs uppercase tracking-wider text-slate-500">All mentions</h3>
            <ul className="space-y-2">
              {mentions.map((m, i) => (
                <li key={i} className="rounded-lg bg-ink-800 p-2 text-sm">
                  <span className="text-slate-500">
                    {fmtTs(m.timestamp_ms)} · {m.speaker}
                  </span>
                  <div className="italic">&ldquo;{m.text}&rdquo;</div>
                </li>
              ))}
            </ul>
          </section>
        )}
        <p className="mt-6 text-xs text-slate-500">
          WiseMouth reports observable language patterns only. It does not detect emotions or intent.
        </p>
      </aside>
    </div>
  );
}
