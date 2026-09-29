# 06 Frontend guide

Next.js 14 (App Router) + TypeScript + Tailwind + lucide-react + Recharts. All pages are client components talking to the backend directly.

## Pages (`frontend/app`)

| Route | File | Purpose |
|---|---|---|
| `/` | `page.tsx` | Landing: name, Start Conversation (random 8-char room), Join by code |
| `/meeting/[room]?name=...` | `meeting/[room]/page.tsx` | Renders `MeetingRoom` |
| `/report/[room]` | `report/[room]/page.tsx` | Renders `ReportView` |
| `/history` | `history/page.tsx` | Past conversations |

## Components (`frontend/components`)

| Component | Notes |
|---|---|
| `MeetingRoom` | Layout, tiles, controls, typed-line box, demo/end buttons, banners (connection lost, STT off) |
| `TranscriptPanel` | Live transcript, interim text greyed, signal chips inline per utterance |
| `RadarPanel` / `LiveSignalCard` | 7 animated counters + latest signal with Earlier/Now evidence |
| `SignalDrawer` | Full evidence for a signal (speaker, time, confidence, topic, related, mentions) |
| `SignalChip` | Coloured label; renders `<button>` only when clickable |
| `ReportView` | Summary, Recharts bar, timeline, annotated transcript |

## Hooks (`frontend/hooks`)

- `useMeetingSocket(room, name)` - WebSocket lifecycle, reconnect with backoff, reducer holding transcript/partials/signals/latest/participants/caps. Returns `{state, sendJSON, sendAudio, startDemo}`.
- `useMic(onFrame)` - `getUserMedia`, `AudioWorklet` (`public/audio-worklet.js`), level meter, mute, camera preview, error messages (permission denied).

## Shared lib (`frontend/lib`)

- `types.ts` - mirrors backend contracts.
- `signals.ts` - `SIGNAL_META` (label, colour, Tailwind classes), `SIGNAL_ORDER`, `countSignals`, `fmtTs`, `confidenceLabel`.
- `api.ts` - `API_URL`, `WS_URL`, `getJSON`.

## Styling

Dark theme, `ink-*` palette in `tailwind.config.ts`. **Tailwind must be able to see class strings**: `lib/**` is included in `content` because `SIGNAL_META` holds class names. Add any new class-bearing directory to `content`.

## Audio pipeline

`AudioWorklet` downsamples the mic's native rate to 16 kHz, converts to Int16 and posts 1600-sample (100 ms) frames -> `sendAudio` -> binary WebSocket frame. Mute = disable the track and tell the server.

## Adding a signal type to the UI

1. Add to `SignalType` in `lib/types.ts`.
2. Add colours/labels to `SIGNAL_META` and order in `SIGNAL_ORDER`.
3. The radar, chips, drawer, timeline and report pick it up automatically.

## Env

`NEXT_PUBLIC_API_URL` (build-time for production builds). WebSocket URL is derived by replacing `http` with `ws`.
