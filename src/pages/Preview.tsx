import { Stamp } from "@/components/khata/Stamp";
import { Money } from "@/components/khata/Money";
import { SectionLabel } from "@/components/khata/SectionLabel";
import { SafeBand } from "@/components/khata/SafeBand";
import { CapBar } from "@/components/khata/CapBar";
import { LedgerRow } from "@/components/khata/LedgerRow";
import { TabBar } from "@/components/khata/TabBar";
import { StatePanel } from "@/components/khata/StatePanel";
import { useState } from "react";

export default function Preview() {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6 font-khata bg-khata-paper min-h-screen text-khata-ink">
      <h1 className="text-3xl font-bold text-khata-ink">Khata Components Preview</h1>

      <SectionLabel>Stamp</SectionLabel>
      <div className="flex flex-wrap gap-3">
        <Stamp kind="PAID" />
        <Stamp kind="WARN" />
        <Stamp kind="OVER" />
      </div>

      <SectionLabel>Money</SectionLabel>
      <div className="flex flex-wrap gap-4 text-lg">
        <Money value={123456} sign />
        <Money value={-412} sign />
        <Money value={0} sign />
        <Money value={15000.5} sign />
      </div>

      <SectionLabel>SafeBand</SectionLabel>
      <SafeBand amount={3020} caption="Available this month" note="Based on income minus bills and caps" />

      <SectionLabel>CapBar</SectionLabel>
      <div className="space-y-4">
        <CapBar label="Shopping" spent={1299} cap={1500} stamp="WARN" />
        <CapBar label="Food" spent={412} cap={1500} />
        <CapBar label="Transport" spent={184} cap={500} />
      </div>

      <SectionLabel>LedgerRow</SectionLabel>
      <div className="space-y-0">
        <LedgerRow date="2026-01-15" title="Swiggy" category="Food & Dining" amount={-412} />
        <LedgerRow date="2026-01-10" title="Stipend credit" category="Income" amount={15000} stamp="PAID" />
        <LedgerRow date="2026-01-12" title="Amazon" category="Shopping" amount={-1299} stamp="WARN" />
      </div>

      <SectionLabel>TabBar</SectionLabel>
      <TabBar
        items={[
          { id: "overview", label: "Overview" },
          { id: "spending", label: "Spending" },
          { id: "rules", label: "Rules" },
        ]}
        activeId={activeTab}
        onSelect={setActiveTab}
      />

      <SectionLabel>StatePanel</SectionLabel>
      <div className="grid gap-4 sm:grid-cols-3">
        <StatePanel kind="empty" title="No transactions yet" hint="Pull to refresh after your first sync" actionLabel="Sync now" onAction={() => {}} />
        <StatePanel kind="loading" title="Loading your data…" hint="This usually takes a few seconds" />
        <StatePanel kind="error" title="Something went wrong" hint="Check your connection and try again" actionLabel="Retry" onAction={() => {}} />
      </div>
    </div>
  );
}