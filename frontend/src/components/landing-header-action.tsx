"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getMe } from "@/lib/api";

type AuthState = "loading" | "guest" | "user";

export function LandingHeaderAction() {
  const [authState, setAuthState] = useState<AuthState>("loading");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        await getMe();
        if (!cancelled) {
          setAuthState("user");
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

  if (authState === "loading") {
    return <div className="h-10 w-[148px] rounded-lg border border-[#3b82f6]/20 bg-[#3b82f6]/10" />;
  }

  if (authState === "user") {
    return (
      <Link
        className="rounded-lg bg-[#3b82f6] px-4 py-2 text-sm font-bold text-white transition-all hover:brightness-110"
        href="/dashboard"
      >
        Go to dashboard
      </Link>
    );
  }

  return (
    <Link
      className="rounded-lg bg-[#3b82f6] px-4 py-2 text-sm font-bold text-white transition-all hover:brightness-110"
      href="/login"
    >
      Log In
    </Link>
  );
}
