type StateKind = "empty" | "loading" | "error";

interface StatePanelProps {
  kind: StateKind;
  title: string;
  hint?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function StatePanel({ kind, title, hint, actionLabel, onAction }: StatePanelProps) {
  return (
    <div className="border-2 border-khata-ink rounded-lg p-6 text-center bg-khata-paper">
      <div
        className={`font-khata text-lg mb-2 ${
          kind === "error" ? "text-khata-vermilion" : "text-khata-ink"
        }`}
      >
        {title}
      </div>
      {hint && <div className="text-khata-muted text-sm mb-4">{hint}</div>}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="inline-block bg-khata-ink text-khata-paper font-num text-sm px-4 py-2 hover:bg-khata-ink/80 transition-colors min-h-[44px]"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}