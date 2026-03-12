"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PlatformShell } from "@/components/platform-shell";
import { ApiError, getAccountWatchlist, type AccountWatchlistItem } from "@/lib/api";

function severityClass(value: string) {
  if (/critical|high/i.test(value)) return "text-rose-400";
  if (/medium|watch|review/i.test(value)) return "text-amber-400";
  return "text-emerald-400";
}

export function WatchlistBoard() {
  const [items, setItems] = useState<AccountWatchlistItem[]>([]);
  const [mode, setMode] = useState<"loading" | "guest" | "ready" | "error">("loading");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const nextItems = await getAccountWatchlist();
        if (!cancelled) {
          setItems(nextItems);
          setMode("ready");
        }
      } catch (error) {
        if (!cancelled) {
          if (error instanceof ApiError && error.status === 401) {
            setMode("guest");
          } else {
            setMode("error");
          }
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <PlatformShell
      actions={[
        { href: "/dashboard", label: "Dashboard", tone: "secondary" },
        { href: "/coins", label: "Open launch feed" },
      ]}
      eyebrow="Watchlist"
      stats={[
        { label: "Tracked entities", value: String(items.length) },
        { label: "Escalations", value: String(items.filter((item) => /high|critical|review/i.test(item.state)).length) },
        { label: "Fresh updates", value: String(items.filter((item) => /just now|m|h/i.test(item.refreshed_at)).length) },
      ]}
      subtitle="A compact pulse board for entities saved to your account watchlist."
      title="Changes across tracked entities"
    >
      {mode === "loading" ? (
        <section className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-8 text-center text-slate-400">
          Loading your watchlist...
        </section>
      ) : null}

      {mode === "guest" ? (
        <section className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-8 text-center">
          <h2 className="text-2xl font-semibold text-slate-100">Sign in to use watchlist</h2>
          <p className="mt-3 text-sm text-slate-400">
            Saved tokens are now tied to your account, so you need to be logged in to view or manage them.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link className="rounded-lg bg-[#2563eb] px-5 py-3 text-sm font-bold text-white" href="/login">
              Log In
            </Link>
            <Link className="rounded-lg border border-[rgba(59,130,246,0.2)] px-5 py-3 text-sm font-semibold text-slate-200" href="/register">
              Register
            </Link>
          </div>
        </section>
      ) : null}

      {mode === "error" ? (
        <section className="rounded-[24px] border border-[rgba(248,113,113,0.25)] bg-[rgba(127,29,29,0.14)] p-8 text-center text-rose-200">
          Unable to load your watchlist right now.
        </section>
      ) : null}

      {mode === "ready" && items.length === 0 ? (
        <section className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-8 text-center">
          <h2 className="text-2xl font-semibold text-slate-100">No tracked tokens yet</h2>
          <p className="mt-3 text-sm text-slate-400">
            Open a token report and hit Watchlist. Saved tokens will start showing up here.
          </p>
          <Link className="mt-6 inline-flex rounded-lg bg-[#2563eb] px-5 py-3 text-sm font-bold text-white" href="/coins">
            Open launch feed
          </Link>
        </section>
      ) : null}

      {mode === "ready" && items.length > 0 ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => (
            <article
              key={`${item.entity_type}-${item.entity_id}`}
              className="rounded-[20px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-6 shadow-[0_20px_60px_rgba(2,6,23,0.18)]"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <strong className="block text-xl text-slate-100">{item.name}</strong>
                  <p className="mt-1 text-xs uppercase tracking-[0.14em] text-slate-500">
                    {item.symbol ? `${item.symbol} · ` : ""}
                    {item.entity_id.slice(0, 4)}...{item.entity_id.slice(-4)}
                  </p>
                </div>
                <span className={`rounded-full border border-[rgba(59,130,246,0.18)] bg-[rgba(59,130,246,0.08)] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.12em] ${severityClass(item.state)}`}>
                  {item.state}
                </span>
              </div>
              <p className="mt-4 text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Latest signal</p>
              <strong className="mt-2 block text-lg text-slate-100">{item.delta}</strong>
              <p className="mt-3 text-sm text-slate-400">Updated {item.refreshed_at}</p>
              {item.report_id ? (
                <Link
                  className="mt-6 inline-flex rounded-lg bg-[rgba(59,130,246,0.14)] px-4 py-2 text-sm font-semibold text-[#93c5fd]"
                  href={`/report/${item.entity_type}/${item.report_id}`}
                >
                  Open report
                </Link>
              ) : null}
            </article>
          ))}
        </section>
      ) : null}
    </PlatformShell>
  );
}
