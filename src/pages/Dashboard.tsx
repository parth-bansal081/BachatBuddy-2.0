import { useCallback, useEffect, useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { BankSyncButton } from "@/components/BankSyncButton";
import { useSetuCallback } from "@/hooks/useSetuCallback";
import { StatePanel } from "@/components/khata/StatePanel";
import { SafeBand } from "@/components/khata/SafeBand";
import { SectionLabel } from "@/components/khata/SectionLabel";
import { LedgerRow } from "@/components/khata/LedgerRow";
import { TabBar } from "@/components/khata/TabBar";
import { tabs } from "@/components/khata/tabs";
import { getNewestTransactionMonth, calculateMonthlySpendPaise, formatPaiseAsInr, type EnrichedTxn } from "@/lib/ledger";
import { useNavigate } from "react-router-dom";

type Txn = EnrichedTxn;

// Phase 0 dashboard: only proves the Setu round trip. Real UI comes later.
export default function Dashboard() {
  const [txns, setTxns] = useState<Txn[]>([]);
  const [state, setState] = useState<"loading" | "error" | "empty" | "ready">("loading");
  const navigate = useNavigate();

  const load = useCallback(async () => {
    setState("loading");
    try {
      const { data, error } = await supabase
        .from("transactions_enriched")
        .select("id,date,amount,merchant,enriched_merchant,enriched_category")
        .order("date", { ascending: false })
        .limit(50);
      if (error) throw error;
      const rows = (data ?? []) as Txn[];
      setTxns(rows);
      setState(rows.length === 0 ? "empty" : "ready");
    } catch (err: unknown) {
      console.error("Load error:", err);
      setState("error");
    }
  }, []);

  useSetuCallback(load);

  useEffect(() => {
    void load();
  }, [load]);

  const handleRetry = () => {
    void load();
  };

  const month = getNewestTransactionMonth(txns);
  const monthKey = month ? month.split(" ")[1] + "-" + month.split(" ")[0].slice(0, 3).toLowerCase() : "";
  const { totalPaise, count } = month ? calculateMonthlySpendPaise(txns, monthKey) : { totalPaise: 0, count: 0 };

  return (
    <div className="mx-auto max-w-sm space-y-4 p-4 bg-khata-paper min-h-screen font-khata text-khata-ink">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-khata-ink">खाता</h1>
        <BankSyncButton />
      </div>

      {/* SafeBand - SPENT this month */}
      {month && (
        <SafeBand
          amount={totalPaise / 100}
          label={`SPENT · ${month}`}
          caption={`${count} transaction${count !== 1 ? "s" : ""} this month`}
        />
      )}

      {/* States */}
      {state === "loading" && <StatePanel kind="loading" title="Loading your ledger…" />}
      {state === "error" && (
        <StatePanel
          kind="error"
          title="Failed to load"
          hint="Check your connection and try again"
          actionLabel="Retry"
          onAction={handleRetry}
        />
      )}
      {state === "empty" && (
        <StatePanel
          kind="empty"
          title="No transactions yet"
          hint="Pull to refresh after your first sync"
          actionLabel="Sync now"
          onAction={handleRetry}
        />
      )}

      {/* Ledger */}
      {state === "ready" && (
        <>
          <SectionLabel>RECENT</SectionLabel>
          <div className="space-y-0">
            {txns.map((t) => (
              <LedgerRow
                key={t.id}
                date={new Date(t.date).toLocaleDateString("en-GB", { day: "2-digit", month: "short" }).toUpperCase()}
                title={t.enriched_merchant ?? t.merchant ?? "—"}
                category={t.enriched_category ?? "—"}
                amount={t.amount}
              />
            ))}
          </div>
        </>
      )}

      {/* TabBar */}
      <TabBar
        items={tabs}
        activeId="dashboard"
        onSelect={(id) => navigate(`/${id}`)}
      />
    </div>
  );
}
