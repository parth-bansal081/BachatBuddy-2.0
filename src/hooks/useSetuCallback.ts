import { useCallback, useEffect } from "react";
import { toast } from "sonner";
import { supabase } from "@/integrations/supabase/client";
import { FORWARD_SETU_PARAMS } from "@/config/setuFlow";

export function useSetuCallback(load: () => Promise<void>) {
  useEffect(() => {
    // === SETU CALLBACK HANDLING: same logic as the old app's Dashboard. Do not change. ===
    const triggerSync = async (consentId: string) => {
      window.history.replaceState({}, "", "/dashboard");
      const toastId = toast.loading("Syncing your financial data...");
      try {
        const { error } = await supabase.functions.invoke("sync-bank-data", {
          body: { mode: "FETCH_DATA", consentId },
        });
        if (error) throw error;
        toast.success("Financial data synced!", { id: toastId });
        await load();
      } catch (err: unknown) {
        console.error("Sync error:", err);
        toast.error("Sync failed: " + (err instanceof Error ? err.message : "Unknown error"), { id: toastId });
      }
    };

    const handleSetuCallback = async () => {
      const params = new URLSearchParams(window.location.search);
      const urlConsentId = params.get("id") || params.get("consentId");
      const success = params.get("success");

      if (urlConsentId && success === "true") {
        sessionStorage.removeItem("setu_consent_pending");
        await triggerSync(urlConsentId);
      } else if (urlConsentId && !success) {
        sessionStorage.setItem("setu_consent_pending", window.location.search);
      }
    };
    // === END SETU CALLBACK HANDLING ===

    void handleSetuCallback();
  }, [load]);
}