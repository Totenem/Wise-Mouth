import { Signal, SignalType } from "./types";

export const SIGNAL_ORDER: SignalType[] = [
  "uncertainty",
  "hedging",
  "commitment",
  "commitment_change",
  "repeated_concern",
  "disagreement",
  "unanswered_question",
];

export const SIGNAL_META: Record<SignalType, { label: string; radar: string; color: string; dot: string; chip: string }> = {
  uncertainty: { label: "UNCERTAINTY", radar: "Uncertainty", color: "#fbbf24", dot: "bg-amber-400", chip: "border-amber-400/40 bg-amber-400/10 text-amber-300" },
  hedging: { label: "HEDGED AGREEMENT", radar: "Hedging", color: "#fb923c", dot: "bg-orange-400", chip: "border-orange-400/40 bg-orange-400/10 text-orange-300" },
  commitment: { label: "COMMITMENT", radar: "Commitments", color: "#34d399", dot: "bg-emerald-400", chip: "border-emerald-400/40 bg-emerald-400/10 text-emerald-300" },
  commitment_change: { label: "COMMITMENT CHANGED", radar: "Commitment Changes", color: "#f87171", dot: "bg-red-400", chip: "border-red-400/40 bg-red-400/10 text-red-300" },
  repeated_concern: { label: "REPEATED CONCERN", radar: "Repeated Concerns", color: "#c084fc", dot: "bg-purple-400", chip: "border-purple-400/40 bg-purple-400/10 text-purple-300" },
  disagreement: { label: "UNRESOLVED DISAGREEMENT", radar: "Disagreements", color: "#38bdf8", dot: "bg-sky-400", chip: "border-sky-400/40 bg-sky-400/10 text-sky-300" },
  unanswered_question: { label: "UNANSWERED QUESTION", radar: "Unanswered Questions", color: "#cbd5e1", dot: "bg-slate-300", chip: "border-slate-300/40 bg-slate-300/10 text-slate-200" },
};

// Resolved disagreements / answered questions no longer count on the radar.
export function countSignals(signals: Iterable<Signal>): Record<SignalType, number> {
  const out = Object.fromEntries(SIGNAL_ORDER.map((t) => [t, 0])) as Record<SignalType, number>;
  for (const s of signals) {
    if (s.status === "resolved" && (s.type === "unanswered_question" || s.type === "disagreement")) continue;
    out[s.type] += 1;
  }
  return out;
}

export function fmtTs(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(s / 3600);
  const m = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
  const sec = String(s % 60).padStart(2, "0");
  return h ? `${h}:${m}:${sec}` : `${m}:${sec}`;
}

export function confidenceLabel(c: number): string {
  return c >= 0.85 ? "High" : c >= 0.7 ? "Medium" : "Low";
}
