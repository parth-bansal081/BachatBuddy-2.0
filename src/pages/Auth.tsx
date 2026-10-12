import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { supabase } from "@/integrations/supabase/client";

export default function Auth() {
  const navigate = useNavigate();
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isSignUp) {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { full_name: fullName } },
        });
        if (error) throw error;
        toast.success("Account created. You can sign in now.");
        setIsSignUp(false);
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        // Setu: if the user was sent away mid-link, resume the callback after login.
        const setuPending = sessionStorage.getItem("setu_consent_pending");
        sessionStorage.removeItem("setu_consent_pending");
        navigate(setuPending ? `/dashboard${setuPending}` : "/dashboard");
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-sm p-6">
      <h1 className="mb-4 text-2xl font-bold">{isSignUp ? "Create account" : "Sign in"}</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        {isSignUp && (
          <input
            className="w-full rounded-md border border-input p-2"
            placeholder="Full name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        )}
        <input
          className="w-full rounded-md border border-input p-2"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="w-full rounded-md border border-input p-2"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-primary p-2 text-primary-foreground disabled:opacity-50"
        >
          {loading ? "Please wait..." : isSignUp ? "Sign up" : "Sign in"}
        </button>
      </form>
      <button className="mt-3 text-sm underline" onClick={() => setIsSignUp(!isSignUp)}>
        {isSignUp ? "Have an account? Sign in" : "New here? Create an account"}
      </button>
    </div>
  );
}
