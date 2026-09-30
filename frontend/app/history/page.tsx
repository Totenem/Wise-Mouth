"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { HttpError, getJSON } from "@/lib/api";
import { HistorySkeleton } from "@/components/Skeletons";

interface Row {
  id: string;
  title: string;
  started_at: string;
  status: string;
}

export default function History() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [error, setError] = useState(false);
  const router = useRouter();
  useEffect(() => {
    getJSON<Row[]>("/api/conversations")
      .then(setRows)
      .catch((e) => (e instanceof HttpError && e.status === 401 ? router.replace("/login") : setError(true)));
  }, [router]);
  return (
    <main className="mx-auto max-w-2xl p-6">
      <Link href="/start" className="text-sm text-slate-400 hover:text-slate-100">
        &larr; Back
      </Link>
      <h1 className="mb-4 mt-2 text-2xl font-bold">Past conversations</h1>
      {error && <p className="text-red-300">Could not reach the backend.</p>}
      {!rows && !error && <HistorySkeleton />}
      {rows && rows.length === 0 && (
        <p className="text-slate-500">No conversations yet. Start one and it will show up here.</p>
      )}
      <ul className="space-y-2">
        {rows?.map((r) => (
          <li key={r.id} className="animate-slidein">
            <Link href={`/report/${r.id}`} className="flex items-center justify-between rounded-lg bg-ink-800 px-4 py-3 hover:bg-ink-700">
              <span>{r.title || r.id}</span>
              <span className="text-xs text-slate-400">
                {new Date(r.started_at).toLocaleString()} · {r.status}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
