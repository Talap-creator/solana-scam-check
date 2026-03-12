"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearAccessToken } from "@/lib/auth";
import { ApiError, getUsage, type UserUsage } from "@/lib/api";

function planLabel(plan: string): string {
  if (plan === "pro") {
    return "Pro";
  }
  if (plan === "enterprise") {
    return "Enterprise";
  }
  return "Free";
}

export function DashboardHeaderActions() {
  const router = useRouter();
  const [usage, setUsage] = useState<UserUsage | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const data = await getUsage();
        if (!cancelled) {
          setUsage(data);
        }
      } catch (error) {
        if (!cancelled && error instanceof ApiError && error.status === 401) {
          setUsage(null);
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const onLogout = () => {
    clearAccessToken();
    router.push("/");
    router.refresh();
  };

  return (
    <div className="flex flex-wrap items-center justify-start gap-2 md:justify-end">
      {usage ? (
        <span className="rounded-full border border-[color:var(--border)] bg-white/6 px-4 py-2 text-sm font-semibold text-white/90">
          {planLabel(usage.plan)}: {usage.remaining_today} left today
        </span>
      ) : null}
      <a
        className="rounded-full bg-[linear-gradient(135deg,#11b8ff,#7effc1)] px-5 py-2 text-sm font-bold text-slate-950"
        href="https://t.me/mrtalap"
        rel="noreferrer"
        target="_blank"
      >
        Upgrade
      </a>
      <button
        className="rounded-full border border-[color:var(--border)] bg-white/6 px-5 py-2 text-sm font-bold"
        onClick={onLogout}
        type="button"
      >
        Log out
      </button>
    </div>
  );
}
