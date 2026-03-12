"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AppIcon } from "@/components/app-icon";
import { CoinsFeedAuthActions } from "@/components/coins-feed-auth-actions";
import { ApiError, getLaunchFeed, type LaunchFeedItem, type LaunchFeedQuery } from "@/lib/api";
import { CoinsFeedControls } from "./controls";
import { CoinsFeedHeader } from "./header";
import { CoinsFeedRow } from "./row";
import { CoinsFeedSkeleton } from "./skeleton";
import type { CoinsFeedProps, QueryState } from "./types";
import { buildFilterChips, buildSearchParams, buildStats, mergeLaunchFeedItems, normalizeQueryState, sortLaunchFeedItems } from "./utils";

const REFRESH_INTERVAL_MS = 15000;

export function CoinsFeed({ initialSearchParams }: CoinsFeedProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [queryState, setQueryState] = useState<QueryState>(() => normalizeQueryState(initialSearchParams));
  const [items, setItems] = useState<LaunchFeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newItemsCount, setNewItemsCount] = useState(0);
  const refreshTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const itemCountRef = useRef(50);
  const itemsRef = useRef<LaunchFeedItem[]>([]);

  const syncUrl = useCallback(
    (nextState: QueryState) => {
      const params = buildSearchParams(nextState);
      const url = params.toString() ? `${pathname}?${params.toString()}` : pathname;
      router.replace(url, { scroll: false });
    },
    [pathname, router],
  );

  const requestFeed = useCallback(
    async (mode: "replace" | "append" | "refresh" = "replace") => {
      const baseQuery: LaunchFeedQuery = {
        limit: mode === "refresh" ? Math.max(itemCountRef.current, 50) : 50,
        tab: queryState.tab,
        sort: queryState.sort,
        age: queryState.age,
        liquidity: queryState.liquidity,
        copycat_only: queryState.copycatOnly,
        q: queryState.query,
      };

      try {
        if (mode === "append") setIsLoadingMore(true);
        else if (mode === "refresh") setIsRefreshing(true);
        else setIsLoading(true);

        const payload = await getLaunchFeed({
          ...baseQuery,
          cursor: mode === "append" ? nextCursor : undefined,
        });

        const currentItems = itemsRef.current;
        const currentMints = new Set(currentItems.map((item) => item.mint));
        const insertedCount = payload.items.filter((item) => !currentMints.has(item.mint)).length;

        setItems((current) => {
          const mergedItems =
            mode === "replace"
              ? sortLaunchFeedItems(payload.items)
              : mergeLaunchFeedItems(current, payload.items);

          const targetCount =
            mode === "append"
              ? current.length + payload.items.length
              : mode === "refresh"
                ? Math.max(itemCountRef.current, payload.items.length, 50)
                : Math.max(payload.items.length, 50);

          const nextItems = mergedItems.slice(0, targetCount);
          itemCountRef.current = nextItems.length || 50;
          itemsRef.current = nextItems;
          return nextItems;
        });

        setNewItemsCount(mode === "refresh" ? insertedCount : 0);
        setNextCursor(payload.next_cursor);
        setError(null);
      } catch (requestError) {
        const message = requestError instanceof ApiError ? requestError.message : "Unable to load launch feed.";
        setError(message);
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
        setIsLoadingMore(false);
      }
    },
    [nextCursor, queryState],
  );

  useEffect(() => {
    requestFeed("replace");
  }, [requestFeed]);

  useEffect(() => {
    if (refreshTimerRef.current) clearInterval(refreshTimerRef.current);
    refreshTimerRef.current = setInterval(() => {
      requestFeed("refresh");
    }, REFRESH_INTERVAL_MS);
    return () => {
      if (refreshTimerRef.current) clearInterval(refreshTimerRef.current);
    };
  }, [requestFeed]);

  const updateQueryState = useCallback(
    (patch: Partial<QueryState>) => {
      setExpandedRow(null);
      setQueryState((current) => {
        const nextState = { ...current, ...patch };
        syncUrl(nextState);
        return nextState;
      });
    },
    [syncUrl],
  );

  const stats = useMemo(() => buildStats(items), [items]);
  const filterChips = useMemo(() => buildFilterChips(queryState), [queryState]);

  return (
    <main className="min-h-screen bg-[#0f172a] text-slate-100">
      <div className="relative flex min-h-screen w-full flex-col overflow-x-hidden">
        <header className="sticky top-0 z-50 border-b border-[rgba(59,130,246,0.16)] bg-[rgba(2,6,23,0.84)] backdrop-blur-md">
          <div className="mx-auto flex h-16 w-full max-w-[1600px] items-center justify-between px-6">
            <div className="flex items-center gap-8">
              <Link className="flex items-center gap-3 text-primary" href="/">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[rgba(59,130,246,0.14)]">
                  <AppIcon className="h-5 w-5" name="shield" />
                </div>
                <h2 className="text-xl font-bold tracking-tight text-slate-100">SolanaTrust</h2>
              </Link>
              <nav className="hidden items-center gap-6 md:flex">
                <Link className="text-sm font-medium text-slate-400 transition-colors hover:text-primary" href="/dashboard">
                  Dashboard
                </Link>
                <span className="border-b-2 border-primary pb-1 text-sm font-medium text-slate-100">Launch Feed</span>
              </nav>
            </div>
            <div className="flex items-center gap-3">
              <CoinsFeedAuthActions />
            </div>
          </div>
        </header>

        <div className="mx-auto w-full max-w-[1600px] flex-1 p-6">
          <div className="flex flex-col gap-6">
            <CoinsFeedHeader
              isRefreshing={isRefreshing}
              loadedCount={items.length}
              newItemsCount={newItemsCount}
              onQueryChange={(value) => updateQueryState({ query: value })}
              query={queryState.query}
              stats={stats}
            />

            <CoinsFeedControls filterChips={filterChips} onUpdate={updateQueryState} queryState={queryState} />

            <section className="overflow-hidden rounded-xl border border-primary/20 bg-background-dark shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
              {error ? (
                <div className="px-5 py-16 text-center">
                  <p className="text-lg font-semibold">Feed request failed.</p>
                  <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{error}</p>
                  <button className="mt-5 rounded-lg bg-primary px-5 py-3 text-sm font-bold text-slate-50" onClick={() => requestFeed("replace")} type="button">
                    Retry
                  </button>
                </div>
              ) : isLoading ? (
                <CoinsFeedSkeleton />
              ) : items.length === 0 ? (
                <div className="px-5 py-16 text-center">
                  <p className="text-lg font-semibold">No launches match current filters.</p>
                  <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Try widening age or liquidity filters.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <div className="min-w-[1180px]">
                    <div className="grid grid-cols-[minmax(0,1.7fr)_120px_130px_130px_150px_160px_120px_120px] border-b border-primary/20 bg-primary/10 text-xs font-bold uppercase tracking-widest text-primary">
                      <div className="px-6 py-4">Token</div>
                      <div className="px-6 py-4">Age</div>
                      <div className="px-6 py-4">Liquidity</div>
                      <div className="px-6 py-4">Market Cap</div>
                      <div className="px-6 py-4">Rug Risk</div>
                      <div className="px-6 py-4">Trade Caution</div>
                      <div className="px-6 py-4">Launch Quality</div>
                      <div className="px-6 py-4">Status</div>
                    </div>

                    {items.map((item) => (
                      <CoinsFeedRow
                        key={item.report_id}
                        expanded={expandedRow === item.report_id}
                        item={item}
                        onToggle={() => setExpandedRow((current) => (current === item.report_id ? null : item.report_id))}
                      />
                    ))}
                  </div>
                </div>
              )}

              {!error && !isLoading ? (
                <div className="flex flex-col gap-3 border-t border-primary/20 px-4 py-4 md:flex-row md:items-center md:justify-between md:px-5">
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {nextCursor ? "More rows available in the current feed window." : "End of current feed window."}
                  </p>
                  <div className="flex items-center gap-3">
                    <button
                      className="rounded-lg border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-semibold text-primary"
                      onClick={() => requestFeed("refresh")}
                      type="button"
                    >
                      {isRefreshing ? "Refreshing..." : "Refresh"}
                    </button>
                    <button
                      className="rounded-lg bg-primary px-5 py-3 text-sm font-bold text-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={!nextCursor || isLoadingMore}
                      onClick={() => requestFeed("append")}
                      type="button"
                    >
                      {isLoadingMore ? "Loading..." : nextCursor ? "Load more" : "No more rows"}
                    </button>
                  </div>
                </div>
              ) : null}
            </section>
          </div>
        </div>

        <footer className="mt-auto border-t border-primary/20 bg-background-dark p-6">
          <div className="mx-auto flex max-w-[1600px] flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-2">
              <span className="text-sm font-black uppercase tracking-widest text-primary">SolanaTrust</span>
              <span className="text-xs font-mono text-slate-500">(c) 2024 DECENTRALIZED DATA PROTOCOL</span>
            </div>
            <div className="flex gap-8 text-xs font-bold uppercase tracking-widest text-slate-400">
              <span>Documentation</span>
              <span>API Keys</span>
              <span>Legal</span>
              <span>Discord</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex flex-col items-end">
                <span className="text-[10px] uppercase text-slate-500">System Status</span>
                <span className="text-[10px] font-bold uppercase text-primary">All Systems Operational</span>
              </div>
              <div className="h-2 w-2 rounded-full bg-primary" />
            </div>
          </div>
        </footer>
      </div>
    </main>
  );
}
