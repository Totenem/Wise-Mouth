"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useRouter } from "next/navigation";
import { HttpError, getJSON } from "@/lib/api";
import { SIGNAL_META, SIGNAL_ORDER, countSignals, fmtTs } from "@/lib/signals";
import { Segment, Signal } from "@/lib/types";
import { SignalChip } from "./SignalChip";
import { SignalDrawer } from "./SignalDrawer";
import { ReportSkeleton } from "./Skeletons";
import { useTheme } from "@/lib/theme";

interface Conversation {
  id: string;
  status: string;
  transcript: Segment[];
  signals: Signal[];
}

export function ReportView({ id }: { id: string }) {
  const light = useTheme() === "light";
  const axis = light ? "#475569" : "#64748b";
  const router = useRouter();
  const [data, setData] = useState<Conversation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<Signal | null>(null);

  useEffect(() => {
    getJSON<Conversation>(`/api/conversations/${id}`)
      .then(setData)
      .catch((e) => (e instanceof HttpError && e.status === 401 ? router.replace("/login") : setError("Conversation not found.")));
  }, [id, router]);

  const signals = useMemo(() => [...(data?.signals ?? [])].sort((a, b) => a.timestamp_ms - b.timestamp_ms), [data]);
  const counts = useMemo(() => countSignals(signals), [signals]);
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const chart = SIGNAL_ORDER.map((t) => ({ name: SIGNAL_META[t].radar, value: counts[t], color: SIGNAL_META[t].color }));
  const highlight = (seg: Segment) => signals.filter((s) => s.speaker === seg.speaker && s.timestamp_ms === seg.start_ms);

  if (error) return <div className="p-8 text-red-300">{error}</div>;
  if (!data) return <ReportSkeleton />;

  return (
    <main className="mx-auto max-w-6xl animate-slidein p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-400">WiseMouth Report</div>
          <h1 className="text-2xl font-bold">Conversation {id}</h1>
        </div>
        <Link href="/start" className="rounded-lg border border-ink-600 px-4 py-2 text-sm hover:bg-ink-700">
          New conversation
        </Link>
      </div>

      <section className="mb-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-ink-700 bg-ink-900 p-4">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Summary · {total} signals</h2>
          <ul className="space-y-1.5">
            {SIGNAL_ORDER.map((t) => (
              <li key={t} className="flex items-center justify-between rounded-lg bg-ink-800 px-3 py-1.5 text-sm">
                <span className="flex items-center gap-2">
                  <span className={`h-2.5 w-2.5 rounded-full ${SIGNAL_META[t].dot}`} />
                  {SIGNAL_META[t].radar}
                </span>
                <span className="font-semibold tabular-nums">{counts[t]}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-ink-700 bg-ink-900 p-4">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Signal mix</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart} layout="vertical" margin={{ left: 30 }}>
                <XAxis type="number" allowDecimals={false} stroke={axis} />
                <YAxis type="category" dataKey="name" width={130} stroke={axis} fontSize={11} />
                <Tooltip
                  cursor={{ fill: light ? "#e8edf5" : "#1a2233" }}
                  contentStyle={{
                    background: light ? "#ffffff" : "#0c101a",
                    border: `1px solid ${light ? "#cbd5e1" : "#263148"}`,
                    color: light ? "#0f172a" : "#e2e8f0",
                  }}
                />
                <Bar dataKey="value" radius={4} isAnimationActive={false}>
                  {chart.map((c) => (
                    <Cell key={c.name} fill={c.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="mb-6 rounded-2xl border border-ink-700 bg-ink-900 p-4">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Timeline</h2>
        {signals.length === 0 ? (
          <p className="text-sm text-slate-500">No signals were detected in this conversation.</p>
        ) : (
          <ol className="relative space-y-2 border-l border-ink-600 pl-5">
            {signals.map((s) => (
              <li key={s.id} className="relative">
                <span className={`absolute -left-[26px] top-2 h-2.5 w-2.5 rounded-full ${SIGNAL_META[s.type].dot}`} />
                <button onClick={() => setOpen(s)} className="flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-left hover:bg-ink-800">
                  <span className="w-12 shrink-0 text-sm tabular-nums text-slate-400">{fmtTs(s.timestamp_ms)}</span>
                  <SignalChip type={s.type} count={s.count} />
                  <span className="min-w-0 flex-1 truncate text-sm text-slate-300">
                    {s.speaker}: &ldquo;{s.evidence}&rdquo;
                  </span>
                </button>
              </li>
            ))}
          </ol>
        )}
      </section>

      <section className="rounded-2xl border border-ink-700 bg-ink-900 p-4">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Transcript</h2>
        <div className="space-y-3">
          {data.transcript.map((t) => (
            <div key={t.id}>
              <div className="text-xs text-slate-500">
                <span className="font-semibold text-slate-300">{t.speaker}</span> · {fmtTs(t.start_ms)}
              </div>
              <p>{t.text}</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {highlight(t).map((s) => (
                  <SignalChip key={s.id} type={s.type} count={s.count} onClick={() => setOpen(s)} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
      <SignalDrawer signal={open} onClose={() => setOpen(null)} />
    </main>
  );
}
