"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const [isSignup, setIsSignup] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { login, signup } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      if (isSignup) {
        await signup(username, email, password);
      } else {
        await login(email, password);
      }
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex-1 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="font-serif text-3xl text-paper mb-1">
            {isSignup ? "Say hello" : "Welcome back"}
          </h1>
          <p className="text-muted text-sm">
            {isSignup
              ? "Create an account to start talking"
              : "Log in to pick up where you left off"}
          </p>
        </div>

        <div className="bg-panel border border-white/5 rounded-2xl p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignup && (
              <div>
                <label className="block text-xs text-muted mb-1.5">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="w-full bg-ink border border-white/10 rounded-lg px-3 py-2 text-paper placeholder:text-muted/60 outline-none focus:border-amber transition-colors"
                />
              </div>
            )}

            <div>
              <label className="block text-xs text-muted mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-ink border border-white/10 rounded-lg px-3 py-2 text-paper placeholder:text-muted/60 outline-none focus:border-amber transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs text-muted mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full bg-ink border border-white/10 rounded-lg px-3 py-2 text-paper placeholder:text-muted/60 outline-none focus:border-amber transition-colors"
              />
            </div>

            {error && <p className="text-danger text-sm">{error}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-amber hover:bg-amber-hover text-ink rounded-lg py-2.5 font-medium transition-colors disabled:opacity-50"
            >
              {submitting ? "Please wait…" : isSignup ? "Create account" : "Log in"}
            </button>
          </form>
        </div>

        <p className="text-sm text-center mt-5 text-muted">
          {isSignup ? "Already have an account?" : "Don't have an account?"}{" "}
          <button
            onClick={() => setIsSignup(!isSignup)}
            className="text-teal hover:underline"
          >
            {isSignup ? "Log in" : "Sign up"}
          </button>
        </p>
      </div>
    </div>
  );
}