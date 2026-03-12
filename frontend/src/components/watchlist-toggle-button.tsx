"use client";

import { useRouter } from "next/navigation";
import { startTransition, useEffect, useState } from "react";
import { AppIcon } from "@/components/app-icon";
import {
  addAccountWatchlistItem,
  ApiError,
  getAccountWatchlistStatus,
  removeAccountWatchlistItem,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

type WatchlistToggleButtonProps = {
  displayName: string;
  entityId: string;
  entityType: "token" | "wallet" | "project";
};

export function WatchlistToggleButton({
  displayName,
  entityId,
  entityType,
}: WatchlistToggleButtonProps) {
  const router = useRouter();
  const [isTracked, setIsTracked] = useState(false);
  const [isPending, setIsPending] = useState(false);

  useEffect(() => {
    let cancelled = false;

    if (!getAccessToken()) {
      setIsTracked(false);
      return;
    }

    const load = async () => {
      try {
        const tracked = await getAccountWatchlistStatus(entityType, entityId);
        if (!cancelled) {
          setIsTracked(tracked);
        }
      } catch {
        if (!cancelled) {
          setIsTracked(false);
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [entityId, entityType]);

  const onToggle = () => {
    if (!getAccessToken()) {
      router.push("/login");
      return;
    }

    setIsPending(true);

    startTransition(async () => {
      try {
        if (isTracked) {
          await removeAccountWatchlistItem(entityType, entityId);
          setIsTracked(false);
        } else {
          await addAccountWatchlistItem(entityType, entityId, displayName);
          setIsTracked(true);
        }
        router.refresh();
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          router.push("/login");
        }
      } finally {
        setIsPending(false);
      }
    });
  };

  return (
    <button
      aria-pressed={isTracked}
      className={
        isTracked
          ? "flex items-center justify-center gap-2 rounded-lg border border-[#60a5fa]/45 bg-[linear-gradient(135deg,rgba(59,130,246,0.24),rgba(96,165,250,0.16))] px-6 py-2 font-bold text-white shadow-[0_0_26px_rgba(59,130,246,0.28)] transition-all hover:brightness-110"
          : "flex items-center justify-center gap-2 rounded-lg border border-[#334155] bg-[#1e293b] px-6 py-2 font-bold text-slate-100 transition-all hover:bg-[#334155]"
      }
      disabled={isPending}
      onClick={onToggle}
      type="button"
    >
      <AppIcon className={`h-5 w-5 ${isTracked ? "text-[#93c5fd]" : "text-slate-200"}`} name={isTracked ? "star-filled" : "star"} />
      {isPending ? (isTracked ? "Removing..." : "Saving...") : isTracked ? "On Watchlist" : "Watchlist"}
    </button>
  );
}
