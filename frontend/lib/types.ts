// Mirrors backend/app/schemas/events.py - change both together.
export type SignalType =
  | "uncertainty"
  | "hedging"
  | "commitment"
  | "commitment_change"
  | "repeated_concern"
  | "disagreement"
  | "unanswered_question";

export interface Ref {
  speaker: string;
  text: string;
  timestamp_ms: number;
}

export interface Signal {
  id: string;
  type: SignalType;
  speaker: string;
  evidence: string;
  timestamp_ms: number;
  confidence: number;
  summary: string;
  topic: string | null;
  related: Ref | null;
  status: "active" | "resolved";
  count: number;
  participants: string[];
  meta: Record<string, unknown>;
}

export interface Segment {
  id: string;
  speaker: string;
  text: string;
  start_ms: number;
}

export interface Participant {
  name: string;
  muted: boolean;
}

export type ServerEvent =
  | { type: "state_snapshot" | "session_ended"; room: string; status: string; participants: Participant[]; transcript: Segment[]; signals: Signal[]; capabilities: { stt: boolean; llm: string }; you?: string }
  | { type: "transcript_partial"; speaker: string; text: string; start_ms: number }
  | ({ type: "transcript_final" } & Segment)
  | { type: "signal" | "signal_update"; signal: Signal }
  | { type: "participants"; participants: Participant[] }
  | { type: "error"; message: string; source?: string }
  | { type: "demo_finished" };
