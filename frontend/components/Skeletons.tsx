"use client";
import { Skeleton, StatusLine as Status } from "./Loading";

const panel = "rounded-2xl border border-ink-700 bg-ink-900 p-4";

export function HistorySkeleton() {
  return (
    <div className="space-y-3">
      <Status messages={["Fetching your conversations...", "Sorting the newest first...", "Almost there..."]} />
      <ul className="space-y-2">
        {[0, 1, 2, 3].map((i) => (
          <li key={i} className="flex items-center justify-between rounded-lg bg-ink-800 px-4 py-3">
            <Skeleton className={i % 2 ? "h-4 w-40" : "h-4 w-56"} />
            <Skeleton className="h-3 w-32" />
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ReportSkeleton() {
  return (
    <main className="mx-auto max-w-6xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div className="space-y-2">
          <div className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-400">WiseMouth Report</div>
          <Skeleton className="h-7 w-64" />
        </div>
        <Skeleton className="h-9 w-40 rounded-lg" />
      </div>
      <div className="mb-4">
        <Status
          messages={["Loading your report...", "Gathering the transcript...", "Lining up signals with their evidence..."]}
        />
      </div>
      <section className="mb-6 grid gap-4 lg:grid-cols-2">
        <div className={panel}>
          <Skeleton className="mb-3 h-3 w-40" />
          <div className="space-y-1.5">
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-8 w-full rounded-lg" />
            ))}
          </div>
        </div>
        <div className={panel}>
          <Skeleton className="mb-3 h-3 w-28" />
          <Skeleton className="h-64 w-full rounded-lg" />
        </div>
      </section>
      <section className={`mb-6 ${panel}`}>
        <Skeleton className="mb-3 h-3 w-24" />
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      </section>
      <section className={panel}>
        <Skeleton className="mb-3 h-3 w-24" />
        <TranscriptLines count={4} />
      </section>
    </main>
  );
}

export function TranscriptLines({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="space-y-1.5">
          <Skeleton className="h-3 w-28" />
          <Skeleton className={i % 2 ? "h-4 w-3/5" : "h-4 w-4/5"} />
        </div>
      ))}
    </div>
  );
}

/** Shown in the meeting room until the first state snapshot arrives from the server. */
export function MeetingSkeleton({ room }: { room: string }) {
  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-ink-700 px-4 py-2">
        <div className="flex items-center gap-3">
          <span className="text-sm font-bold tracking-[0.3em] text-emerald-400">WISEMOUTH</span>
          <span className="rounded-md border border-ink-600 px-2 py-0.5 text-xs text-slate-400">{room}</span>
        </div>
        <Skeleton className="h-3 w-48" />
      </header>
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <section className={`flex min-h-0 flex-col gap-3 ${panel}`}>
          <div className="flex gap-2">
            <Skeleton className="h-24 min-w-[8rem] flex-1 rounded-xl" />
            <Skeleton className="hidden h-24 min-w-[8rem] flex-1 rounded-xl sm:block" />
          </div>
          <div className="flex min-h-0 flex-1 flex-col gap-4">
            <Status
              messages={[
                "Connecting to the room...",
                "Waking up the signal engine...",
                "Syncing the transcript...",
                "Still working, the server may be starting up...",
              ]}
            />
            <TranscriptLines count={3} />
          </div>
          <div className="flex justify-center gap-2 border-t border-ink-700 pt-3">
            <Skeleton className="h-9 w-28 rounded-full" />
            <Skeleton className="h-9 w-24 rounded-full" />
            <Skeleton className="h-9 w-44 rounded-full" />
          </div>
        </section>
        <section className={panel}>
          <Skeleton className="mb-2 h-3 w-40" />
          <div className="mb-4 space-y-1.5">
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-8 w-full rounded-lg" />
            ))}
          </div>
          <Skeleton className="mb-2 h-3 w-28" />
          <Skeleton className="h-28 w-full rounded-xl" />
        </section>
      </div>
    </div>
  );
}
