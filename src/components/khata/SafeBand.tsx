import { Money } from "./Money";

interface SafeBandProps {
  amount: number;
  caption: string;
  note?: string;
}

export function SafeBand({ amount, caption, note }: SafeBandProps) {
  return (
    <div className="bg-khata-ink text-khata-paper rounded-lg p-4">
      <div className="text-khata-dim font-num text-xs uppercase tracking-wider mb-1">SAFE TO SPEND</div>
      <div className="font-num text-3xl font-bold">{amount >= 0 ? "+" : ""}{amount.toLocaleString("en-IN")}</div>
      <div className="text-khata-muted text-sm mt-1">{caption}</div>
      {note && <div className="text-khata-dim text-xs mt-1">{note}</div>}
    </div>
  );
}