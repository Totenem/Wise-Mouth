"use client";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Copy, Mic, MicOff, PhoneOff, Play, Send, Video, VideoOff, WifiOff } from "lucide-react";
import { useMeetingSocket } from "@/hooks/useMeetingSocket";
import { useMic } from "@/hooks/useMic";
import { Signal } from "@/lib/types";
import { RadarPanel } from "./RadarPanel";
import { SignalDrawer } from "./SignalDrawer";
import { TranscriptPanel } from "./TranscriptPanel";

function Tile({ name, you, speaking, muted, stream, level }: {
  name: string; you: boolean; speaking: boolean; muted: boolean; stream?: MediaStream | null; level?: number;
}) {
  const ref = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.srcObject = stream ?? null;
  }, [stream]);
  const glow = speaking || (level ?? 0) > 0.12;
  return (
    <div className={`relative flex h-24 min-w-[8rem] flex-1 items-center justify-center overflow-hidden rounded-xl bg-ink-800 ring-2 transition ${glow ? "ring-emerald-400" : "ring-transparent"}`}>
      {stream ? (
        <video ref={ref} autoPlay muted playsInline className="h-full w-full object-cover" />
      ) : (
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-ink-600 text-lg font-semibold">
          {name.slice(0, 1).toUpperCase()}
        </div>
      )}
      <div className="absolute bottom-1 left-2 flex items-center gap-1 text-xs text-slate-200">
        {muted && <MicOff size={12} className="text-red-400" />}
        {name}
        {you ? " (you)" : ""}
      </div>
    </div>
  );
}

export function MeetingRoom({ room, name }: { room: string; name: string }) {
  const router = useRouter();
  const { state, sendJSON, sendAudio, startDemo } = useMeetingSocket(room, name);
  const mic = useMic(sendAudio);
  const [open, setOpen] = useState<Signal | null>(null);
  const [line, setLine] = useState("");
  const [as, setAs] = useState(name);
  const [copied, setCopied] = useState(false);
  const [speaking, setSpeaking] = useState<Record<string, number>>({});
  const [, setTick] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const signals = useMemo(() => Object.values(state.signals).sort((a, b) => a.timestamp_ms - b.timestamp_ms), [state.signals]);
  const ended = state.status === "ended";

  // Mark tiles as "speaking" briefly when their partial/final transcript arrives.
  useEffect(() => {
    const now = Date.now();
    const next = { ...speaking };
    Object.keys(state.partials).forEach((s) => (next[s] = now));
    setSpeaking(next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.partials]);

  useEffect(() => {
    if (ended) {
      mic.stop();
      const t = setTimeout(() => router.push(`/report/${room}`), 1200);
      return () => clearTimeout(t);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ended]);

  const submit = () => {
    if (!line.trim()) return;
    sendJSON({ type: "say", speaker: as.trim() || name, text: line.trim() });
    setLine("");
  };

  const names = new Set(state.participants.map((p) => p.name));
  const virtual = Array.from(new Set(state.transcript.map((t) => t.speaker))).filter((s) => !names.has(s));

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-ink-700 px-4 py-2">
        <div className="flex items-center gap-3">
          <span className="text-sm font-bold tracking-[0.3em] text-emerald-400">WISEMOUTH</span>
          <button
            onClick={() => { navigator.clipboard?.writeText(room); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
            className="flex items-center gap-1 rounded-md border border-ink-600 px-2 py-0.5 text-xs text-slate-300 hover:bg-ink-700"
            title="Copy room code"
          >
            <Copy size={12} /> {copied ? "Copied" : room}
          </button>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span>{state.caps.stt ? "Speech: AssemblyAI" : "Speech: off (type or demo)"}</span>
          <span>Analysis: {state.caps.llm || "rules-only"}</span>
        </div>
      </header>

      {(state.error || mic.error || !state.connected) && (
        <div className="flex items-center gap-2 bg-red-500/15 px-4 py-1.5 text-sm text-red-300">
          <WifiOff size={14} /> {state.error || mic.error || "Connecting..."}
          {!state.caps.stt && state.connected && <span className="text-red-200/70"> Use the demo conversation instead.</span>}
        </div>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <section className="flex min-h-0 flex-col gap-3 rounded-2xl border border-ink-700 bg-ink-900 p-4">
          <div className="flex gap-2 overflow-x-auto">
            {state.participants.map((p) => (
              <Tile key={p.name} name={p.name} you={p.name === state.you} muted={p.muted} stream={p.name === state.you ? mic.camera : null}
                speaking={Date.now() - (speaking[p.name] ?? 0) < 2500} level={p.name === state.you && !mic.muted ? mic.level : 0} />
            ))}
            {virtual.map((v) => (
              <Tile key={v} name={v} you={false} muted={false} speaking={Date.now() - (speaking[v] ?? 0) < 2500} />
            ))}
          </div>

          <div className="min-h-0 flex-1">
            <TranscriptPanel transcript={state.transcript} partials={state.partials} signals={signals} live={!ended} onOpen={setOpen} />
          </div>

          {!ended && (
            <div className="flex gap-2">
              <input value={as} onChange={(e) => setAs(e.target.value)} aria-label="Speaking as"
                className="w-28 rounded-lg border border-ink-600 bg-ink-800 px-2 py-2 text-sm outline-none focus:border-emerald-400" />
              <input value={line} onChange={(e) => setLine(e.target.value)} onKeyDown={(e) => e.key === "Enter" && submit()}
                placeholder="Type a line as this speaker..."
                className="min-w-0 flex-1 rounded-lg border border-ink-600 bg-ink-800 px-3 py-2 text-sm outline-none focus:border-emerald-400" />
              <button onClick={submit} aria-label="Send line" className="rounded-lg bg-ink-700 px-3 hover:bg-ink-600"><Send size={16} /></button>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-center gap-2 border-t border-ink-700 pt-3">
            {!mic.active ? (
              <button onClick={mic.start} disabled={!state.caps.stt || ended}
                title={state.caps.stt ? "Start microphone" : "Set ASSEMBLYAI_API_KEY on the backend to enable speech"}
                className="flex items-center gap-2 rounded-full bg-emerald-500 px-4 py-2 text-sm font-semibold text-ink-950 hover:bg-emerald-400 disabled:opacity-40">
                <Mic size={16} /> Start mic
              </button>
            ) : (
              <button onClick={() => sendJSON({ type: mic.toggleMute() ? "mute" : "unmute" })}
                className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold ${mic.muted ? "bg-red-500/80" : "bg-ink-700 hover:bg-ink-600"}`}>
                {mic.muted ? <MicOff size={16} /> : <Mic size={16} />} {mic.muted ? "Unmute" : "Mute"}
              </button>
            )}
            <button onClick={mic.toggleCamera} className="flex items-center gap-2 rounded-full bg-ink-700 px-4 py-2 text-sm hover:bg-ink-600">
              {mic.camera ? <VideoOff size={16} /> : <Video size={16} />} Camera
            </button>
            <button onClick={startDemo} disabled={state.demoRunning || ended || !state.connected}
              className="flex items-center gap-2 rounded-full border border-emerald-400/50 px-4 py-2 text-sm text-emerald-300 hover:bg-emerald-400/10 disabled:opacity-40">
              <Play size={16} /> {state.demoRunning ? "Demo running..." : "Run demo conversation"}
            </button>
            <button onClick={() => sendJSON({ type: "end" })} disabled={ended}
              className="flex items-center gap-2 rounded-full bg-red-600 px-4 py-2 text-sm font-semibold hover:bg-red-500 disabled:opacity-40">
              <PhoneOff size={16} /> End &amp; view report
            </button>
          </div>
        </section>

        <section className="min-h-0 overflow-hidden rounded-2xl border border-ink-700 bg-ink-900 p-4">
          <RadarPanel signals={state.signals} latest={state.latest} onOpen={setOpen} />
        </section>
      </div>
      <SignalDrawer signal={open} onClose={() => setOpen(null)} />
    </div>
  );
}
