import type { ReactNode } from "react";

interface SectionLabelProps {
  children: ReactNode;
}

export function SectionLabel({ children }: SectionLabelProps) {
  return (
    <div className="border-t-2 border-khata-ink pt-2 text-khata-muted font-num text-xs uppercase tracking-wider">
      {children}
    </div>
  );
}