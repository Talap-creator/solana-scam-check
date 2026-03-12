"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getMe } from "@/lib/api";

type AuthState = "loading" | "guest" | "user" | "admin";

export function SiteHeader() {
  const [authState, setAuthState] = useState<AuthState>("loading");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const profile = await getMe();
        if (!cancelled) {
          setAuthState(profile.role === "admin" ? "admin" : "user");
        }
      } catch {
        if (!cancelled) {
          setAuthState("guest");
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <header className="mb-7 flex flex-col gap-4 rounded-[24px] border border-[color:var(--border)] bg-[rgba(2,6,23,0.72)] px-5 py-4 shadow-[0_20px_60px_rgba(2,6,23,0.34)] backdrop-blur md:flex-row md:items-center md:justify-between">
      <a className="flex items-center gap-3 text-[var(--accent)]" href="#top">
        <span className="grid h-10 w-10 place-items-center rounded-xl border border-[rgba(59,130,246,0.24)] bg-[rgba(59,130,246,0.12)] font-[family:var(--font-display)] text-lg font-bold text-[var(--accent)]">
          R
        </span>
        <span className="flex flex-col">
          <strong className="text-base font-bold tracking-tight text-slate-100">RugSignal</strong>
          <span className="text-xs text-slate-400">Solana risk intelligence</span>
        </span>
      </a>

      <nav className="flex flex-wrap gap-2 text-sm text-slate-400 md:justify-center">
        {[
          ["#scan", "Intelligence"],
          ["/coins", "Live Feed"],
          ["#pricing", "Pricing"],
          ["#roadmap", "Roadmap"],
        ].map(([href, label]) => (
          <a
            key={href}
            className="rounded-lg px-3 py-2 transition hover:bg-[rgba(59,130,246,0.08)] hover:text-[var(--accent)]"
            href={href}
          >
            {label}
          </a>
        ))}
      </nav>

      <div className="flex flex-wrap gap-2 sm:gap-3">
        {authState === "guest" ? (
          <>
            <Link
              className="rounded-lg border border-[color:var(--border)] bg-white/5 px-5 py-2.5 text-center text-sm font-bold text-slate-100"
              href="/login"
            >
              Login
            </Link>
            <Link
              className="rounded-lg bg-[var(--accent)] px-5 py-2.5 text-center text-sm font-bold text-white shadow-[0_0_24px_rgba(59,130,246,0.24)]"
              href="/register"
            >
              Register
            </Link>
          </>
        ) : null}

        {authState === "user" ? (
          <Link
            className="rounded-lg border border-[color:var(--border)] bg-white/5 px-5 py-2.5 text-center text-sm font-bold text-slate-100"
            href="/dashboard"
          >
            Dashboard
          </Link>
        ) : null}

        {authState === "admin" ? (
          <Link
            className="rounded-lg border border-[color:var(--border)] bg-white/5 px-5 py-2.5 text-center text-sm font-bold text-slate-100"
            href="/admin"
          >
            Admin panel
          </Link>
        ) : null}

      </div>
    </header>
  );
}
