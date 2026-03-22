"use client";

import { useEffect, useState } from "react";
import { PremiumCheckoutButton } from "@/components/premium-checkout-button";
import { ApiError, getUsage, type UserUsage } from "@/lib/api";
import { formatPlanLabel } from "@/lib/plans";

export function AccountUsageBanner() {
  const [usage, setUsage] = useState<UserUsage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const data = await getUsage();
        if (!cancelled) {
          setUsage(data);
        }
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        if (loadError instanceof ApiError && loadError.status === 401) {
          setUsage(null);
          return;
        }
        setError("Unable to load scan limits right now.");
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <section className="mb-6 rounded-[24px] border border-[color:var(--border)] bg-[var(--panel)] px-4 py-3 text-sm text-[var(--muted)]">
        {error}
      </section>
    );
  }

  if (!usage) {
    return null;
  }

  const percent = usage.daily_limit > 0 ? Math.min(100, (usage.used_today / usage.daily_limit) * 100) : 0;
  const nearLimit = usage.remaining_today <= Math.max(1, Math.floor(usage.daily_limit * 0.2));
  const exhausted = usage.remaining_today <= 0;
  const sourceText = usage.limit_source === "custom" ? "Custom admin limit" : "Plan limit";
  const resetAt = new Date(usage.reset_at).toLocaleString();

  return (
    <section
      className={`mb-6 rounded-[24px] border px-4 py-4 md:px-5 ${
        exhausted
          ? "border-[var(--critical)] bg-[rgba(255,123,120,0.1)]"
          : nearLimit
            ? "border-[#ffd566] bg-[rgba(255,213,102,0.08)]"
            : "border-[color:var(--border)] bg-[var(--panel)]"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-extrabold tracking-[0.16em] text-[var(--accent-deep)]">ACCOUNT USAGE</p>
          <h2 className="mt-1 text-xl font-bold">{formatPlanLabel(usage.plan)} plan limits</h2>
        </div>
        {(nearLimit || exhausted) && usage.plan === "free" ? (
          <PremiumCheckoutButton
            className="rounded-full bg-[linear-gradient(135deg,#2563eb,#38bdf8)] px-4 py-2 text-sm font-bold text-white"
            label="Upgrade plan"
          />
        ) : null}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <article className="rounded-2xl border border-[color:var(--border)] bg-white/6 px-4 py-3">
          <p className="text-xs text-[var(--muted)]">Used today</p>
          <strong className="mt-1 block text-2xl">{usage.used_today}</strong>
        </article>
        <article className="rounded-2xl border border-[color:var(--border)] bg-white/6 px-4 py-3">
          <p className="text-xs text-[var(--muted)]">Daily limit</p>
          <strong className="mt-1 block text-2xl">{usage.daily_limit}</strong>
        </article>
        <article className="rounded-2xl border border-[color:var(--border)] bg-white/6 px-4 py-3">
          <p className="text-xs text-[var(--muted)]">Remaining</p>
          <strong className="mt-1 block text-2xl">{usage.remaining_today}</strong>
        </article>
      </div>

      <p className="mt-3 text-sm text-[var(--muted)]">
        {sourceText}. Resets at {resetAt}.
      </p>
      <div
        aria-valuemax={100}
        aria-valuemin={0}
        aria-valuenow={Math.round(percent)}
        className="mt-3 h-2 rounded-full bg-white/10"
        role="progressbar"
      >
        <div
          className={`h-2 rounded-full ${
            exhausted
              ? "bg-[var(--critical)]"
              : nearLimit
                ? "bg-[#99660e]"
                : "bg-[linear-gradient(135deg,#11b8ff,#7effc1)]"
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </section>
  );
}
