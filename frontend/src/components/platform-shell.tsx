"use client";

import Link from "next/link";
import { ReactNode } from "react";

type ShellAction = {
  href: string;
  label: string;
  tone?: "primary" | "secondary";
};

type ShellStat = {
  label: string;
  value: string;
};

type PlatformShellProps = {
  actions?: ShellAction[];
  children: ReactNode;
  eyebrow: string;
  headerContent?: ReactNode;
  subtitle: string;
  title: string;
  stats?: ShellStat[];
};

function ShieldMark() {
  return (
    <svg aria-hidden="true" className="h-5 w-4" viewBox="0 0 16 20" fill="none">
      <path
        d="M8 1.25 13.5 3v5.04c0 4.09-2.63 7.7-6.5 8.96C3.13 15.74.5 12.13.5 8.04V3L8 1.25Z"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <path
        d="M8 5.1 10.8 6v2.44c0 2-1.2 3.78-2.8 4.33-1.6-.55-2.8-2.33-2.8-4.33V6L8 5.1Z"
        fill="currentColor"
        opacity="0.35"
      />
    </svg>
  );
}

export function PlatformShell({
  actions = [],
  children,
  eyebrow,
  headerContent,
  subtitle,
  title,
  stats = [],
}: PlatformShellProps) {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#020617] text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(59,130,246,0.14),transparent_28%),linear-gradient(180deg,#020617_0%,#0b1328_52%,#020617_100%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-40 [background-image:linear-gradient(rgba(37,99,235,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(37,99,235,0.06)_1px,transparent_1px)] [background-size:72px_72px]" />

      <div className="relative">
        <header className="sticky top-0 z-40 border-b border-[rgba(59,130,246,0.16)] bg-[rgba(2,6,23,0.8)] backdrop-blur-md">
          <div className="mx-auto flex h-16 w-full max-w-[1440px] items-center justify-between px-4 sm:px-6 lg:px-10">
            <div className="flex items-center gap-8">
              <Link className="flex items-center gap-3 text-[#3b82f6]" href="/">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[rgba(59,130,246,0.14)]">
                  <ShieldMark />
                </span>
                <span className="text-xl font-bold tracking-[-0.04em] text-slate-100">SolanaTrust</span>
              </Link>

              <nav className="hidden items-center gap-6 md:flex">
                <Link className="text-sm font-medium text-slate-400 transition-colors hover:text-[#3b82f6]" href="/dashboard">
                  Dashboard
                </Link>
                <Link className="text-sm font-medium text-slate-400 transition-colors hover:text-[#3b82f6]" href="/coins">
                  Launch Feed
                </Link>
                <Link className="text-sm font-medium text-slate-400 transition-colors hover:text-[#3b82f6]" href="/history">
                  History
                </Link>
                <Link className="text-sm font-medium text-slate-400 transition-colors hover:text-[#3b82f6]" href="/watchlist">
                  Watchlist
                </Link>
              </nav>
            </div>

            <div className="flex items-center gap-3">
              {headerContent ??
                actions.map((action) => (
                  <Link
                    key={`${action.href}-${action.label}`}
                    className={
                      action.tone === "secondary"
                        ? "rounded-lg border border-[rgba(59,130,246,0.2)] bg-[rgba(59,130,246,0.06)] px-4 py-2 text-sm font-semibold text-slate-200 transition-colors hover:bg-[rgba(59,130,246,0.12)]"
                        : "rounded-lg bg-[#2563eb] px-4 py-2 text-sm font-bold text-white shadow-[0_12px_24px_rgba(37,99,235,0.25)] transition-all hover:brightness-110"
                    }
                    href={action.href}
                  >
                    {action.label}
                  </Link>
                ))}
            </div>
          </div>
        </header>

        <div className="mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6 lg:px-10">
          <section className="rounded-[28px] border border-[rgba(59,130,246,0.16)] bg-[linear-gradient(180deg,rgba(15,23,42,0.82),rgba(15,23,42,0.68))] p-6 shadow-[0_24px_80px_rgba(2,6,23,0.28)]">
            <p className="text-xs font-extrabold uppercase tracking-[0.24em] text-[#60a5fa]">{eyebrow}</p>
            <h1 className="mt-3 max-w-4xl font-[family:var(--font-display)] text-4xl font-black tracking-[-0.06em] text-slate-100 md:text-6xl">
              {title}
            </h1>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 md:text-base">{subtitle}</p>

            {stats.length > 0 ? (
              <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                {stats.map((stat) => (
                  <article
                    key={stat.label}
                    className="rounded-[18px] border border-[rgba(59,130,246,0.16)] bg-[rgba(59,130,246,0.06)] px-4 py-4"
                  >
                    <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">
                      {stat.label}
                    </span>
                    <strong className="mt-2 block text-2xl text-slate-100">{stat.value}</strong>
                  </article>
                ))}
              </div>
            ) : null}
          </section>

          <div className="mt-6">{children}</div>
        </div>
      </div>
    </main>
  );
}
