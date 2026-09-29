"use client";
import { useCallback, useEffect, useReducer, useRef } from "react";
import { WS_URL, getToken } from "@/lib/api";
import { Participant, Segment, ServerEvent, Signal } from "@/lib/types";

export interface MeetingState {
  connected: boolean;
  status: string;
  you: string;
  participants: Participant[];
  transcript: Segment[];
  partials: Record<string, string>;
  signals: Record<string, Signal>;
  latest: Signal | null;
  caps: { stt: boolean; llm: string };
  error: string | null;
  demoRunning: boolean;
}

const initial: MeetingState = {
  connected: false,
  status: "connecting",
  you: "",
  participants: [],
  transcript: [],
  partials: {},
  signals: {},
  latest: null,
  caps: { stt: false, llm: "" },
  error: null,
  demoRunning: false,
};

type Action = { t: "server"; e: ServerEvent } | { t: "conn"; v: boolean } | { t: "demo"; v: boolean };

function reduce(s: MeetingState, a: Action): MeetingState {
  if (a.t === "conn") {
    return { ...s, connected: a.v, error: a.v || s.status === "ended" ? null : "Connection lost. Reconnecting..." };
  }
  if (a.t === "demo") return { ...s, demoRunning: a.v };
  const e = a.e;
  switch (e.type) {
    case "state_snapshot":
    case "session_ended": {
      const signals = Object.fromEntries(e.signals.map((x) => [x.id, x]));
      return {
        ...s,
        status: e.status,
        you: e.you ?? s.you,
        participants: e.participants,
        transcript: e.transcript,
        signals,
        caps: e.capabilities,
        partials: {},
        error: null,
        latest: s.latest ?? e.signals[e.signals.length - 1] ?? null,
      };
    }
    case "participants":
      return { ...s, participants: e.participants };
    case "transcript_partial":
      return { ...s, partials: { ...s.partials, [e.speaker]: e.text } };
    case "transcript_final": {
      if (s.transcript.some((x) => x.id === e.id)) return s;
      const partials = { ...s.partials };
      delete partials[e.speaker];
      return {
        ...s,
        partials,
        transcript: [...s.transcript, { id: e.id, speaker: e.speaker, text: e.text, start_ms: e.start_ms }],
      };
    }
    case "signal":
    case "signal_update":
      return {
        ...s,
        signals: { ...s.signals, [e.signal.id]: e.signal },
        latest: e.type === "signal" || s.latest?.id === e.signal.id ? e.signal : s.latest,
      };
    case "error":
      return { ...s, error: e.message };
    case "demo_finished":
      return { ...s, demoRunning: false };
  }
  return s;
}

export function useMeetingSocket(room: string, name: string) {
  const [state, dispatch] = useReducer(reduce, initial);
  const wsRef = useRef<WebSocket | null>(null);
  const closedRef = useRef(false);
  const statusRef = useRef("connecting");
  statusRef.current = state.status;

  useEffect(() => {
    closedRef.current = false;
    let retry = 1000;
    let timer: ReturnType<typeof setTimeout>;
    const connect = () => {
      const ws = new WebSocket(`${WS_URL}/ws/meeting/${room}`);
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;
      ws.onopen = () => {
        retry = 1000;
        ws.send(JSON.stringify({ type: "join", name, token: getToken() }));
        dispatch({ t: "conn", v: true });
      };
      ws.onmessage = (m) => {
        if (typeof m.data === "string") dispatch({ t: "server", e: JSON.parse(m.data) });
      };
      ws.onclose = (ev) => {
        dispatch({ t: "conn", v: false });
        if (ev.code === 4401) {  // not signed in and room doesn't exist yet
          closedRef.current = true;
          window.location.href = "/login";
          return;
        }
        if (!closedRef.current && statusRef.current !== "ended") {
          timer = setTimeout(connect, retry);
          retry = Math.min(retry * 2, 8000);
        }
      };
    };
    connect();
    return () => {
      closedRef.current = true;
      clearTimeout(timer);
      wsRef.current?.close();
    };
  }, [room, name]);

  const sendJSON = useCallback((o: object) => {
    if (wsRef.current?.readyState === 1) wsRef.current.send(JSON.stringify(o));
  }, []);
  const sendAudio = useCallback((b: ArrayBuffer) => {
    if (wsRef.current?.readyState === 1) wsRef.current.send(b);
  }, []);
  const startDemo = useCallback(() => {
    if (wsRef.current?.readyState !== 1) return;
    dispatch({ t: "demo", v: true });
    sendJSON({ type: "demo_start" });
  }, [sendJSON]);
  return { state, sendJSON, sendAudio, startDemo };
}
