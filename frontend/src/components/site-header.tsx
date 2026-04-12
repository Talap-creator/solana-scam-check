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
      <Link className="flex items-center gap-3 text-[var(--accent)]" href="/">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[rgba(59,130,246,0.14)]">
          <svg aria-hidden="true" className="h-5 w-4 text-[#3b82f6]" viewBox="0 0 16 20" fill="none">
            <path d="M8 1.25 13.5 3v5.04c0 4.09-2.63 7.7-6.5 8.96C3.13 15.74.5 12.13.5 8.04V3L8 1.25Z" stroke="currentColor" strokeWidth="1.6" />
            <path d="M8 5.1 10.8 6v2.44c0 2-1.2 3.78-2.8 4.33-1.6-.55-2.8-2.33-2.8-4.33V6L8 5.1Z" fill="currentColor" opacity="0.35" />
          </svg>
        </span>
        <span className="text-xl font-bold tracking-[-0.04em] text-slate-100">SolanaTrust</span>
      </Link>

      <nav className="flex flex-wrap gap-2 text-sm text-slate-400 md:justify-center">
        {[
          ["#scan", "Intelligence"],
          ["/coins", "Live Feed"],
          ["/oracle", "Oracle"],
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
        <a
          className="flex items-center gap-1.5 rounded-lg border border-[color:var(--border)] bg-white/5 px-4 py-2.5 text-sm font-bold text-slate-100 transition hover:bg-white/10"
          href="https://github.com/Talap-creator/solana-scam-check"
          rel="noreferrer"
          target="_blank"
        >
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          GitHub
        </a>
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
