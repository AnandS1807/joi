"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error, clearError } = useAuthStore();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    clearError();
    try {
      await register(email, password, fullName);
      router.push("/login");
    } catch {
      // Error is already written to store.
    }
  }

  return (
    <section className="auth-wrap card stack">
      <div>
        <h1>Create Account</h1>
        <p className="muted">Start using resume scoring and matching in minutes.</p>
      </div>

      <form className="stack" onSubmit={onSubmit}>
        <label>
          Full Name
          <input
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Anand Kumar"
          />
        </label>

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
            placeholder="Minimum 8 chars"
            minLength={8}
            required
          />
        </label>

        {error ? <p className="status-warn">{error}</p> : null}

        <button className="btn-primary" disabled={isLoading} type="submit">
          {isLoading ? "Creating..." : "Create Account"}
        </button>
      </form>

      <p className="muted">
        Already registered? <Link href="/login">Sign in</Link>
      </p>
    </section>
  );
}
