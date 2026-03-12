"use client";

import Link from "next/link";
import { type ReactNode, useState } from "react";
import { getAccessToken } from "@/lib/auth";

type AuthPaywallSectionProps = {
  children: ReactNode;
  title?: string;
  description?: string;
};

export function AuthPaywallSection({
  children,
  title = "Unlock full access",
  description = "Create a free account to view full analytics details.",
}: AuthPaywallSectionProps) {
  const [isAuthed] = useState(() => Boolean(getAccessToken()));

  if (isAuthed) {
    return <>{children}</>;
  }

  return (
    <div className="relative">
      <div className="pointer-events-none blur-[3px]">{children}</div>
      <div className="absolute inset-0 grid place-items-center rounded-[28px] bg-[rgba(4,12,20,0.76)] p-4 text-center backdrop-blur-sm">
        <div className="max-w-md rounded-[28px] border border-[color:var(--border)] bg-[linear-gradient(180deg,rgba(12,29,45,0.96),rgba(7,18,29,0.92))] p-6 shadow-[0_24px_70px_rgba(0,0,0,0.4)]">
          <p className="text-sm font-bold text-[var(--accent-deep)]">{title}</p>
          <p className="mt-2 text-sm text-[var(--muted)]">{description}</p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            <Link
              className="rounded-full bg-[linear-gradient(135deg,#11b8ff,#7effc1)] px-4 py-2 text-sm font-bold text-slate-950"
              href="/register"
            >
              Register
            </Link>
            <Link
              className="rounded-full border border-[color:var(--border)] bg-white/6 px-4 py-2 text-sm font-bold"
              href="/login"
            >
              Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
