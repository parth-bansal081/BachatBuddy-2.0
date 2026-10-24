import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import type { Session } from "@supabase/supabase-js";
import { Toaster } from "sonner";
import { supabase } from "@/integrations/supabase/client";
import Auth from "@/pages/Auth";
import Dashboard from "@/pages/Dashboard";
import LoadingInsights from "@/pages/LoadingInsights";
import Preview from "@/pages/Preview";
import Policy from "@/pages/Policy";

function Protected({ session, children }: { session: Session | null; children: ReactNode }) {
  if (!session) return <Navigate to="/auth" replace />;
  return <>{children}</>;
}

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    void supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setReady(true);
    });
    const { data } = supabase.auth.onAuthStateChange((_event, next) => setSession(next));
    return () => data.subscription.unsubscribe();
  }, []);

  if (!ready) return <p className="p-6">Loading...</p>;

  return (
    <>
      <Toaster />
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/auth" element={<Auth />} />
        <Route
          path="/dashboard"
          element={
            <Protected session={session}>
              <Dashboard />
            </Protected>
          }
        />
        <Route
          path="/loading-insights"
          element={
            <Protected session={session}>
              <LoadingInsights />
            </Protected>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
        {import.meta.env.DEV && (
          <Route
            path="/preview"
            element={
              <Protected session={session}>
                <Preview />
              </Protected>
            }
          />
        )}
        <Route
          path="/policy"
          element={
            <Protected session={session}>
              <Policy />
            </Protected>
          }
        />
      </Routes>
    </>
  );
}
