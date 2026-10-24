import type { StampKind } from "./Stamp";
import { Stamp } from "./Stamp";

interface LedgerRowProps {
  date: string;
  title: string;
  category: string;
  amount: number;
  stamp?: StampKind;
}

export function LedgerRow({ date, title, category, amount, stamp }: LedgerRowProps) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-khata-ink gap-2">
      <div className="flex-1 min-w-0">
        <div className="font-khata text-khata-ink truncate">{title}</div>
        <div className="font-num text-xs text-khata-muted">{category}</div>
      </div>
      <div className="flex items-center gap-2 font-num text-khata-ink">
        <span className="text-right whitespace-nowrap">
          {amount >= 0 ? "+" : ""}{amount.toLocaleString("en-IN")}
        </span>
        {stamp && <Stamp kind={stamp} />}
      </div>
    </div>
  );
}