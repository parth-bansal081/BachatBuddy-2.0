import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { AppShell } from "@/components/khata/AppShell";
import { KButton } from "@/components/khata/KButton";
import { SectionLabel } from "@/components/khata/SectionLabel";
import { SafeBand } from "@/components/khata/SafeBand";
import { LedgerRow } from "@/components/khata/LedgerRow";
import { CapBar } from "@/components/khata/CapBar";
import { StatePanel } from "@/components/khata/StatePanel";
import { Stamp } from "@/components/khata/Stamp";
import { formatInr } from "@/lib/format";
import {
  api,
  type CompileResult,
  type Policy,
  type Rule,
  type BacktestResult,
} from "@/lib/api";

export default function Policy() {
  const navigate = useNavigate();
  const [text, setText] = useState("");
  const [compileState, setCompileState] = useState<"idle" | "loading" | "error" | "success">("idle");
  const [compileError, setCompileError] = useState("");
  const [compileResult, setCompileResult] = useState<CompileResult | null>(null);
  const [backtestState, setBacktestState] = useState<"idle" | "loading" | "error" | "success">("idle");
  const [backtestError, setBacktestError] = useState("");
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [saveState, setSaveState] = useState<"idle" | "loading" | "error" | "success">("idle");
  const [saveError, setSaveError] = useState("");
  const [activePolicy, setActivePolicy] = useState<{ policy: Policy; source_text: string } | null>(null);
  const [activePolicyLoaded, setActivePolicyLoaded] = useState(false);

  const loadActivePolicy = useCallback(async () => {
    try {
      const res = await api.active();
      if (res.policy) {
        setActivePolicy({ policy: res.policy, source_text: res.source_text ?? "" });
      }
    } catch (err: unknown) {
      console.error("Failed to load active policy:", err);
    } finally {
      setActivePolicyLoaded(true);
    }
  }, []);

  useEffect(() => {
    loadActivePolicy();
  }, [loadActivePolicy]);

  const handleCompile = async () => {
    setCompileState("loading");
    setCompileError("");
    try {
      const res = await api.compile(text);
      setCompileResult(res);
      if (res.ok) {
        setCompileState("success");
      } else {
        setCompileState("error");
        setCompileError(res.message ?? "Could not compile rule");
      }
    } catch (err: unknown) {
      setCompileState("error");
      setCompileError(err instanceof Error ? err.message : "Compile failed");
    }
  };

  const handleBacktest = async () => {
    if (!compileResult?.policy) return;
    setBacktestState("loading");
    setBacktestError("");
    try {
      const res = await api.backtest(compileResult.policy);
      setBacktestResult(res);
      setBacktestState("success");
    } catch (err: unknown) {
      setBacktestState("error");
      setBacktestError(err instanceof Error ? err.message : "Backtest failed");
    }
  };

  const handleSave = async () => {
    if (!compileResult?.policy) return;
    setSaveState("loading");
    setSaveError("");
    try {
      await api.save(compileResult.policy, text);
      setSaveState("success");
    } catch (err: unknown) {
      setSaveState("error");
      setSaveError(err instanceof Error ? err.message : "Save failed");
    }
  };

  const formatRule = (rule: Rule): string => {
    if (rule.type === "save_percent") {
      return `${rule.label}: ${rule.percent}% of every income credit`;
    }
    if (rule.type === "category_cap") {
      return `${rule.category} capped at ${formatInr(rule.monthly_limit)}/month`;
    }
    return `${rule.name}: ${formatInr(rule.amount)} reserved for the ${rule.due_day}${getOrdinal(rule.due_day)} of each month`;
  };

  return (
    <AppShell>
      <div className="space-y-4">
        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-khata-ink">Policy</h1>
          <p className="text-khata-muted text-sm font-khata">Write a rule in plain words. Hinglish works.</p>
        </div>

        {/* Compose area */}
        <div className="bg-khata-paper border-2 border-khata-ink rounded-lg p-4 space-y-3">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="e.g. save 10% of every income, keep food under 3000 a month"
            rows={3}
            className="w-full bg-khata-paper border-2 border-khata-ink rounded font-khata text-khata-ink placeholder:text-khata-dim text-sm p-2 resize-none focus:outline-none focus:ring-2 focus:ring-khata-vermilion"
            disabled={compileState === "loading"}
          />
          <KButton
            variant="primary"
            onClick={handleCompile}
            disabled={compileState === "loading" || text.trim().length === 0}
          >
            {compileState === "loading" ? "Compiling…" : "COMPILE"}
          </KButton>
        </div>

        {/* Compile error */}
        {compileState === "error" && (
          <StatePanel
            kind="error"
            title="Compile failed"
            hint={compileError}
            actionLabel="Retry"
            onAction={handleCompile}
          />
        )}

        {/* Compile success - show rules and backtest button */}
        {compileState === "success" && compileResult?.ok && compileResult.policy && (
          <>
            <SectionLabel>RULES</SectionLabel>
            <div className="space-y-2 bg-khata-paper border-2 border-khata-ink rounded-lg p-4">
              {compileResult.policy.rules.map((rule, i) => (
                <div key={i} className="font-khata text-khata-ink text-sm">
                  {formatRule(rule)}
                </div>
              ))}
              {compileResult.unsupported.length > 0 && (
                <div className="mt-2 space-y-1">
                  <div className="text-khata-vermilion font-num text-xs">Unsupported:</div>
                  {compileResult.unsupported.map((u, i) => (
                    <div key={i} className="text-khata-muted text-xs">• {u}</div>
                  ))}
                </div>
              )}
            </div>
            <KButton
              variant="outline"
              onClick={handleBacktest}
              disabled={backtestState === "loading"}
            >
              {backtestState === "loading" ? "Running backtest…" : "BACKTEST"}
            </KButton>

            {/* Backtest error */}
            {backtestState === "error" && (
              <StatePanel
                kind="error"
                title="Backtest failed"
                hint={backtestError}
                actionLabel="Retry"
                onAction={handleBacktest}
              />
            )}

            {/* Backtest success */}
            {backtestState === "success" && backtestResult && (
              <>
                <SectionLabel>BACKTEST</SectionLabel>
                <SafeBand
                  amount={backtestResult.headline ? parseFloat(backtestResult.headline.match(/₹?([\d,]+)/)?.[1]?.replace(/,/g, "") ?? "0") : backtestResult.total_saved}
                  label="EST. SAVED"
                  caption={`${backtestResult.months.length} month${backtestResult.months.length !== 1 ? "s" : ""} tested`}
                />
                <div className="space-y-2">
                  {backtestResult.months.map((month) => (
                    <CapBar
                      key={month.month}
                      label={month.month}
                      spent={month.spend}
                      cap={month.caps.reduce((sum, c) => sum + c.limit, 0)}
                    />
                  ))}
                  {backtestResult.events.map((event, i) => (
                    <LedgerRow
                      key={i}
                      date={event.day.slice(5, 7) + " " + event.day.slice(0, 4)}
                      title={event.detail}
                      category={event.kind}
                      amount={event.amount}
                    />
                  ))}
                  <div className="text-khata-muted text-xs font-khata">
                    {backtestResult.warnings.map((w, i) => (
                      <div key={i}>Warning: {w}</div>
                    ))}
                  </div>
                </div>

                {/* Save button */}
                <KButton
                  variant="primary"
                  onClick={handleSave}
                  disabled={saveState === "loading"}
                >
                  {saveState === "loading" ? "Saving…" : "SAVE POLICY"}
                </KButton>

                {/* Save error */}
                {saveState === "error" && (
                  <StatePanel
                    kind="error"
                    title="Save failed"
                    hint={saveError}
                    actionLabel="Retry"
                    onAction={handleSave}
                  />
                )}

                {/* Save success */}
                {saveState === "success" && (
                  <div className="flex items-center justify-center gap-2 text-khata-vermilion">
                    <Stamp kind="PAID" />
                    <span className="font-khata text-sm">Saved</span>
                  </div>
                )}
              </>
            )}
          </>
        )}

        {/* Active Policy */}
        {activePolicyLoaded && (
          <SectionLabel>ACTIVE POLICY</SectionLabel>
        )}
        {activePolicyLoaded && activePolicy && (
          <div className="bg-khata-paper border-2 border-khata-ink rounded-lg p-4 space-y-2">
            <div className="font-khata text-khata-ink text-sm font-bold">{activePolicy.policy.name}</div>
            {activePolicy.policy.rules.map((rule, i) => (
              <div key={i} className="font-khata text-khata-ink text-sm">{formatRule(rule)}</div>
            ))}
            {activePolicy.source_text && (
              <div className="text-khata-dim text-xs font-khata mt-2">From: "{activePolicy.source_text}"</div>
            )}
          </div>
        )}
        {activePolicyLoaded && !activePolicy && (
          <StatePanel kind="empty" title="No active policy yet" hint="Write a rule above and save it" />
        )}
      </div>
    </AppShell>
  );
}

function getOrdinal(n: number): string {
  if (n === 11 || n === 12 || n === 13) return "th";
  switch (n % 10) {
    case 1:
      return "st";
    case 2:
      return "nd";
    case 3:
      return "rd";
    default:
      return "th";
  }
}