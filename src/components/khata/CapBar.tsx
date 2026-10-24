import type { StampKind } from "./Stamp";
import { Stamp } from "./Stamp";

interface CapBarProps {
  label: string;
  spent: number;
  cap: number;
  stamp?: StampKind;
}

export function CapBar({ label, spent, cap, stamp }: CapBarProps) {
  const ratio = cap > 0 ? Math.min(Math.max(spent / cap, 0), 1) : 0;
  const pct = Math.round(ratio * 100);
  const isWarn = ratio >= 0.8;

  return (
    <div className="flex items-center gap-3">
      <div className="w-24 text-right font-num text-sm text-khata-muted">{label}</div>
      <div className="flex-1 relative h-6 bg-khata-dim/30 border border-khata-ink rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            isWarn ? "bg-khata-vermilion" : "bg-khata-ink"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="w-28 text-right font-num text-sm text-khata-ink">
        {spent.toLocaleString("en-IN")} / {cap.toLocaleString("en-IN")}
      </div>
      {stamp && <Stamp kind={stamp} />}
    </div>
  );
}