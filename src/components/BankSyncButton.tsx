import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Landmark, ShieldCheck, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
// Removed supabase import as it is handled by the service now, but kept it just in case.
import { supabase } from "@/integrations/supabase/client";
import { initiateBankSync } from "@/lib/setuService";
import { toast } from "sonner";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";

interface BankSyncButtonProps {
    className?: string;
    size?: "default" | "sm" | "lg" | "icon" | null | undefined;
}

export const BankSyncButton = ({ className, size }: BankSyncButtonProps = {}) => {
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    const handleSync = async () => {
        setIsLoading(true);
        setErrorMsg(null);
        try {
            const consentData = await initiateBankSync();
            if (consentData.url) {
                // Store the consent ID in sessionStorage so that if the user is
                // redirected to /auth before returning, Auth.tsx can route them back
                // to /dashboard with the correct consentId after login.
                if (consentData.consentId) {
                    sessionStorage.setItem(
                        'setu_consent_pending',
                        `?id=${consentData.consentId}&success=true`
                    );
                }
                window.location.assign(consentData.url);
            } else {
                throw new Error("Invalid consent URL received");
            }
        } catch (error: any) {
            console.error("Link Bank error:", error);
            setErrorMsg(error.message || "An unexpected error occurred");
            toast.error("Failed to connect bank");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button
                    variant="outline"
                    size={size || "default"}
                    className={cn(
                        "w-full justify-start gap-3 h-12 px-4 border-dashed border-2 hover:border-primary hover:bg-primary/5 transition-all duration-300",
                        className
                    )}
                >
                    <Landmark className="h-5 w-5 text-primary" />
                    <div className="flex flex-col items-start">
                        <span className="text-sm font-semibold">Link Bank Account</span>
                        <span className="text-xs text-muted-foreground">Via Account Aggregator</span>
                    </div>
                </Button>
            </DialogTrigger>

            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <ShieldCheck className="h-5 w-5 text-primary" />
                        Secure Bank Link
                    </DialogTitle>
                    <DialogDescription>
                        You will be redirected to Onemoney to securely approve data sharing.
                        This follows RBI's Account Aggregator (AA) framework — you control what's shared.
                    </DialogDescription>
                </DialogHeader>

                <div className="py-6 flex flex-col items-center justify-center gap-4">
                    {errorMsg ? (
                        <div className="w-full p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-500 text-sm font-medium text-center animate-in fade-in slide-in-from-bottom-2">
                            Setu Error: {errorMsg}
                        </div>
                    ) : (
                        <div className="p-4 bg-muted rounded-full">
                            <Landmark className="h-10 w-10 text-primary" />
                        </div>
                    )}
                    {!errorMsg && (
                        <div className="space-y-2 text-center">
                            <p className="text-sm text-muted-foreground">
                                BachatBuddy uses 256-bit encryption to ensure your data stays private.
                            </p>
                            <p className="text-xs font-mono bg-primary/5 p-2 rounded border border-primary/10">
                                🛠️ Sandbox Mode: Use Phone <span className="font-bold">9999999999</span> | OTP <span className="font-bold">123456</span>
                            </p>
                        </div>
                    )}
                </div>

                <Button
                    onClick={handleSync}
                    disabled={isLoading}
                    className="w-full py-6 text-lg font-bold bg-primary hover:bg-primary/90"
                >
                    {isLoading ? (
                        <>
                            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                            Connecting...
                        </>
                    ) : (
                        "Proceed to Link"
                    )}
                </Button>
            </DialogContent>
        </Dialog>
    );
};