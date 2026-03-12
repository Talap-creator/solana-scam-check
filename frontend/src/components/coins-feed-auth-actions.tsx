"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearAccessToken } from "@/lib/auth";
import { getMe, logoutUser } from "@/lib/api";

type AuthMode = "loading" | "guest" | "user" | "admin";

export function CoinsFeedAuthActions() {
  const router = useRouter();
  const [authMode, setAuthMode] = useState<AuthMode>("loading");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const profile = await getMe();
        if (!cancelled) {
          setAuthMode(profile.role === "admin" ? "admin" : "user");
        }
      } catch {
        if (!cancelled) {
          setAuthMode("guest");
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
      setAuthMode("guest");
      router.push("/");
      router.refresh();
    }
  };

  if (authMode === "loading") {
    return <div className="hidden h-10 w-[160px] rounded-lg border border-primary/20 bg-primary/10 md:block" />;
  }

  if (authMode === "guest") {
    return (
      <Link className="hidden rounded-lg px-4 py-2 text-sm font-bold text-slate-100 md:inline-flex" href="/login">
        Log In
      </Link>
    );
  }

  return (
    <>
      <Link
        className="hidden rounded-lg border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-bold text-primary md:inline-flex"
        href={authMode === "admin" ? "/admin" : "/dashboard"}
      >
        {authMode === "admin" ? "Admin" : "Dashboard"}
      </Link>
      <button
        className="hidden rounded-lg px-4 py-2 text-sm font-bold text-slate-100 md:inline-flex"
        onClick={() => void onLogout()}
        type="button"
      >
        Log out
      </button>
    </>
  );
}
