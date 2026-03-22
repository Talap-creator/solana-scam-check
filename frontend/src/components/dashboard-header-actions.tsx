"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PremiumCheckoutButton } from "@/components/premium-checkout-button";
import { clearAccessToken } from "@/lib/auth";
import { ApiError, getUsage, logoutUser, type UserUsage } from "@/lib/api";
import { APP_TELEGRAM_URL, formatPlanLabel } from "@/lib/plans";

export function DashboardHeaderActions() {
  const router = useRouter();
  const [usage, setUsage] = useState<UserUsage | null>(null);
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const data = await getUsage();
        if (!cancelled) {
          setHasToken(true);
          setUsage(data);
        }
      } catch (error) {
        if (!cancelled && error instanceof ApiError && error.status === 401) {
          setHasToken(false);
          setUsage(null);
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const onLogout = async () => {
    try {
      await logoutUser();
    } finally {
      clearAccessToken();
      router.push("/");
      router.refresh();
    }
  };

  return (
    <div className="grid w-full gap-2 sm:grid-cols-2 xl:flex xl:w-auto xl:flex-wrap xl:items-center xl:justify-end">
      {usage ? (
        <>
          <span className="rounded-full border border-[color:var(--border)] bg-white/6 px-4 py-2 text-center text-sm font-semibold text-white/90">
            {formatPlanLabel(usage.plan)}
          </span>
          <span className="rounded-full border border-[color:var(--border)] bg-white/6 px-4 py-2 text-center text-sm font-semibold text-white/90">
            {usage.remaining_today} / {usage.daily_limit} requests left
          </span>
        </>
      ) : null}
      <a
        className="rounded-full border border-[color:var(--border)] bg-white/6 px-5 py-2 text-center text-sm font-bold text-white/90 transition hover:border-[rgba(96,165,250,0.35)] hover:bg-white/10"
        href={APP_TELEGRAM_URL}
        rel="noreferrer"
        target="_blank"
      >
        Telegram
      </a>
      {usage?.plan === "free" ? (
        <PremiumCheckoutButton
          className="rounded-full bg-[linear-gradient(135deg,#2563eb,#38bdf8)] px-5 py-2 text-center text-sm font-bold text-white"
          label="Upgrade"
        />
      ) : null}
      {hasToken ? (
        <button
          className="rounded-full border border-[color:var(--border)] bg-white/6 px-5 py-2 text-center text-sm font-bold"
          onClick={() => void onLogout()}
          type="button"
        >
          Log out
        </button>
      ) : null}
    </div>
  );
}
