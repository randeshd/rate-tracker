"use client";

import { useActionState } from "react";
import { login } from "./actions";

export default function LoginPage() {
  const [error, action, pending] = useActionState(login, "");
  return (
    <main className="login">
      <form action={action} className="login-card">
        <h1>Investment Tracker</h1>
        <label htmlFor="password">Password</label>
        <input id="password" name="password" type="password" autoFocus required autoComplete="current-password" />
        {error && <p className="login-error">{error}</p>}
        <button type="submit" disabled={pending}>
          {pending ? "Checking…" : "Enter"}
        </button>
      </form>
    </main>
  );
}
