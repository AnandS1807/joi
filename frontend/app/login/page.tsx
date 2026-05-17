"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login, hydrate, isLoading, error, clearError } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    hydrate();
    if (localStorage.getItem("access_token")) {
      router.replace("/dashboard");
    }
  }, [hydrate, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    clearError();
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch {
      // Error is already written to store.
    }
  }

  return (
    <section className="auth-wrap card stack">
      <div>
        <h1>Welcome Back</h1>
        <p className="muted">Sign in to continue your resume matching workflow.</p>
      </div>

      <form className="stack" onSubmit={onSubmit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            required
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Your password"
            required
          />
        </label>

        {error ? <p className="status-warn">{error}</p> : null}

        <button className="btn-primary" disabled={isLoading} type="submit">
          {isLoading ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <p className="muted">
        No account? <Link href="/register">Create one</Link>
      </p>
    </section>
  );
}
