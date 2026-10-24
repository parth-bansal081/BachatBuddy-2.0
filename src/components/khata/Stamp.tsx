export type StampKind = "PAID" | "WARN" | "OVER";

interface StampProps {
  kind: StampKind;
}

export function Stamp({ kind }: StampProps) {
  return (
    <span
      className="inline-block font-num text-xs uppercase tracking-wider text-khata-vermilion border-2 border-khata-vermilion px-1.5 py-0.5 -rotate-6"
      aria-label={kind}
    >
      {kind}
    </span>
  );
}