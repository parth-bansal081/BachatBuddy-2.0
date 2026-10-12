import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { FORWARD_SETU_PARAMS } from "@/config/setuFlow";

// The Setu redirect lands here (path /loading-insights must stay exactly this).
// Phase 0 placeholder: waits briefly, then goes to /dashboard.
export default function LoadingInsights() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const timer = setTimeout(() => {
      const target = FORWARD_SETU_PARAMS ? `/dashboard${location.search}` : "/dashboard";
      navigate(target, { replace: true });
    }, 2500);
    return () => clearTimeout(timer);
  }, [navigate, location.search]);

  return <p className="p-6 text-sm text-muted-foreground">Connecting to your bank data...</p>;
}
