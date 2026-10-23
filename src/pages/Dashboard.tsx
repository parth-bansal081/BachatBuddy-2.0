import { useCallback, useEffect, useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { BankSyncButton } from "@/components/BankSyncButton";
import { useSetuCallback } from "@/hooks/useSetuCallback";

type Account = { id: string; account_name: string; account_type: string; last_four: string | null };
type Txn = { id: string; date: string; amount: number; category: string | null; merchant: string | null };

// Phase 0 dashboard: only proves the Setu round trip. Real UI comes later.
export default function Dashboard() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [txns, setTxns] = useState<Txn[]>([]);

  const load = useCallback(async () => {
    const acc = await supabase.from("accounts").select("*").order("created_at", { ascending: false });
    setAccounts((acc.data ?? []) as Account[]);
    const tx = await supabase.from("transactions").select("*").order("date", { ascending: false }).limit(25);
    setTxns((tx.data ?? []) as Txn[]);
  }, []);

  useSetuCallback(load);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">BachatBuddy (Phase 0)</h1>
        <button className="text-sm underline" onClick={() => void supabase.auth.signOut()}>
          Sign out
        </button>
      </div>

      <BankSyncButton />

      <section>
        <h2 className="mb-2 font-semibold">Accounts ({accounts.length})</h2>
        <ul className="text-sm">
          {accounts.map((a) => (
            <li key={a.id}>
              {a.account_name} - {a.account_type}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-2 font-semibold">Latest transactions ({txns.length} shown)</h2>
        <ul className="text-sm">
          {txns.map((t) => (
            <li key={t.id}>
              {String(t.date ?? "").slice(0, 10)} | {t.merchant ?? "-"} | {t.category ?? "-"} | {t.amount}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
