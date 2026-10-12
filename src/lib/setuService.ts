/**
 * Setu Account Aggregator Service
 * Handles bank account syncing via Setu's AA API
 */
import { supabase } from "@/integrations/supabase/client";

interface ConsentResponse {
    url: string;
    consentId: string;
    status: string;
}

/**
 * Initiates bank account sync via Setu Account Aggregator
 * Calls the 'create-consent' Edge Function
 */
export async function initiateBankSync(): Promise<ConsentResponse> {
    try {
        const { data: { session } } = await supabase.auth.getSession();
        
        const response = await fetch('https://anminqetakxavgwnvrqa.supabase.co/functions/v1/create-consent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session?.access_token}`
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error("Edge Function Error:", errorText);
            throw new Error(`Edge function returned error ${response.status}`);
        }
        
        const data = await response.json();

        if (!data || !data.url) {
            throw new Error("No consent URL returned from Setu");
        }

        return {
            url: data.url,
            consentId: data.consentId,
            status: data.status,
        };
    } catch (error: any) {
        console.error("Error initiating bank sync:", error);
        throw new Error(error.message || "Failed to initiate bank sync");
    }
}

/**
 * Opens the consent URL in a new window
 */
/**
 * Opens the consent URL in a new tab
 */
export function openConsentWindow(url: string): Window | null {
    return window.open(url, "_blank");
}
