import { formatInr } from "@/lib/format";

export type EnrichedTxn = {
  id: string;
  date: string;
  amount: number;
  merchant: string | null;
  enriched_merchant: string | null;
  enriched_category: string | null;
};

export function getNewestTransactionMonth(txns: EnrichedTxn[]): string | null {
  if (txns.length === 0) return null;
  // Transactions are already sorted newest first
  const newest = txns[0];
  const d = new Date(newest.date);
  return d.toLocaleString("en-GB", { month: "short", year: "numeric" }).toUpperCase();
}

export function calculateMonthlySpendPaise(
  txns: EnrichedTxn[],
  targetMonth: string // "YYYY-MM"
): { totalPaise: number; count: number } {
  let totalPaise = 0;
  let count = 0;

  for (const txn of txns) {
    const amount = txn.amount;
    if (amount >= 0) continue; // credits are positive, debits are negative

    const txnDate = new Date(txn.date);
    const txnMonth = `${txnDate.getFullYear()}-${String(txnDate.getMonth() + 1).padStart(2, "0")}`;
    if (txnMonth !== targetMonth) continue;

    // Round each amount to whole paise before adding
    const paise = Math.round(Math.abs(amount) * 100);
    totalPaise += paise;
    count++;
  }

  return { totalPaise, count };
}

export function formatPaiseAsInr(paise: number): string {
  return formatInr(paise / 100);
}