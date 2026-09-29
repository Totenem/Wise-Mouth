import { SIGNAL_META } from "@/lib/signals";
import { SignalType } from "@/lib/types";

export function SignalChip({ type, onClick, count }: { type: SignalType; onClick?: () => void; count?: number }) {
  const m = SIGNAL_META[type];
  const cls = `inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold tracking-wide ${m.chip}`;
  const body = (
    <>
      <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} />
      {m.label}
      {count && count > 1 ? ` x${count}` : ""}
    </>
  );
  // Render a plain span when not clickable so chips can live inside other buttons.
  return onClick ? (
    <button onClick={onClick} className={`${cls} hover:brightness-125`}>{body}</button>
  ) : (
    <span className={cls}>{body}</span>
  );
}
