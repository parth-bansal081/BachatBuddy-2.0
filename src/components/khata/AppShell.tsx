import type { ReactNode } from "react";
import { TabBar } from "./TabBar";
import { tabs } from "./tabs";
import { useNavigate } from "react-router-dom";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const navigate = useNavigate();

  return (
    <div className="mx-auto max-w-sm min-h-screen bg-khata-paper font-khata text-khata-ink flex flex-col">
      <div className="flex-1 p-4 space-y-4 overflow-auto">{children}</div>
      <TabBar
        items={tabs}
        activeId="dashboard"
        onSelect={(id) => navigate(`/${id}`)}
      />
    </div>
  );
}