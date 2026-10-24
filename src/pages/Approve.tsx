import { useState, useEffect, useCallback } from "react";
import { AppShell } from "@/components/khata/AppShell";
import { KButton } from "@/components/khata/KButton";
import { SectionLabel } from "@/components/khata/SectionLabel";
import { LedgerRow } from "@/components/khata/LedgerRow";
import { Money } from "@/components/khata/Money";
import { StatePanel } from "@/components/khata/StatePanel";
import { api, type ActionOut } from "@/lib/api";
import { buildUpiLink } from "@/lib/upi";

export default function Approve() {
  const [upiId, setUpiId] = useState("");
  const [actions, setActions] = useState<ActionOut[]>([]);
  const [state, setState] = useState<"loading" | "error" | "empty" | "ready">("loading");
  const [error, setError] = useState("");

  const loadUpiId = useCallback(() => {
    try {
      const stored = localStorage.getItem("upi_id");
      if (stored) setUpiId(stored);
    } catch {
      // ignore storage errors
    }
  }, []);

  const saveUpiId = useCallback((id: string) => {
    try {
      localStorage.setItem("upi_id", id);
    } catch {
      // ignore storage errors
    }
  }, []);

  const loadActions = useCallback(async () => {
    setState("loading");
    setError("");
    try {
      const res = await api.actionsPending();
      setActions(res);
      setState(res.length === 0 ? "empty" : "ready");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load actions");
      setState("error");
    }
  }, []);

  const handlePropose = useCallback(async () => {
    setState("loading");
    setError("");
    try {
      const res = await api.actionsGenerate();
      setActions(res.actions);
      setState(res.actions.length === 0 ? "empty" : "ready");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to propose actions");
      setState("error");
    }
  }, []);

  const handleDecide = useCallback(async (id: string, decision: "approved" | "rejected") => {
    try {
      await api.actionsDecide(id, decision);
      loadActions();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Decision failed");
      setState("error");
    }
  }, [loadActions]);

  const getPayLink = (action: ActionOut) => {
    const amount = Number(action.amount);
    const note = `Set-aside: ${action.label} for ${action.month}`;
    return buildUpiLink(upiId, "Self", amount, note);
  };

  useEffect(() => {
    loadUpiId();
    loadActions();
  }, [loadUpiId, loadActions]);

  return (
    <AppShell>
      <div className="space-y-4">
        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-khata-ink">Approve</h1>
          <p className="text-khata-muted text-sm font-khata">Your rules propose; you decide.</p>
        </div>

        {/* UPI ID Input */}
        <div className="bg-khata-paper border-2 border-khata-ink rounded-lg p-4 space-y-3">
          <div className="space-y-1">
            <label className="text-khata-muted font-num text-xs uppercase tracking-wider">
              Your UPI ID
            </label>
            <p className="text-khata-dim text-xs font-khata">
              Where the set-aside should go (your own savings VPA)
            </p>
          </div>
          <input
            type="text"
            value={upiId}
            onChange={(e) => {
              const val = e.target.value;
              setUpiId(val);
              saveUpiId(val);
            }}
            placeholder="yourname@bank"
            className="w-full bg-khata-paper border-2 border-khata-ink rounded font-khata text-khata-ink placeholder:text-khata-dim text-sm p-2 resize-none focus:outline-none focus:ring-2 focus:ring-khata-vermilion"
          />
        </div>

        {/* Propose Button */}
        <KButton
          variant="primary"
          onClick={handlePropose}
          disabled={state === "loading"}
        >
          {state === "loading" ? "Loading…" : "PROPOSE"}
        </KButton>

        {/* Error State */}
        {state === "error" && (
          <StatePanel
            kind="error"
            title="Failed to load"
            hint={error}
            actionLabel="Retry"
            onAction={loadActions}
          />
        )}

        {/* Empty State */}
        {state === "empty" && (
          <StatePanel
            kind="empty"
            title="Nothing to approve"
            hint="Propose from your policy."
            actionLabel="Propose"
            onAction={handlePropose}
          />
        )}

        {/* Actions List */}
        {state === "ready" && (
          <>
            <SectionLabel>PENDING SET-ASIDES</SectionLabel>
            <div className="space-y-2">
              {actions.map((action) => (
                <div
                  key={action.id}
                  className="bg-khata-paper border-2 border-khata-ink rounded-lg p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-khata text-khata-ink text-sm">{action.label}</div>
                      <div className="text-khata-muted font-num text-xs">
                        {action.month}
                      </div>
                    </div>
                    <Money value={Number(action.amount)} sign />
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <KButton
                      variant="primary"
                      onClick={() => handleDecide(action.id, "approved")}
                      disabled={action.status !== "pending"}
                    >
                      APPROVE
                    </KButton>
                    <KButton
                      variant="outline"
                      onClick={() => handleDecide(action.id, "rejected")}
                      disabled={action.status !== "pending"}
                    >
                      REJECT
                    </KButton>
                  </div>
                  {action.status === "approved" && (
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-num text-khata-vermilion text-sm">
                        APPROVED
                      </span>
                      {upiId ? (
                        <a
                          href={getPayLink(action)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block bg-khata-vermilion text-khata-paper font-num text-sm px-3 py-1.5 rounded hover:bg-khata-vermilion/80 transition-colors min-h-[44px] flex items-center"
                        >
                          PAY VIA UPI
                        </a>
                      ) : (
                        <span className="text-khata-dim font-num text-xs">
                          Enter UPI ID to enable payment
                        </span>
                      )}
                    </div>
                  )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </AppShell>
  );
}