import type { StatCard } from "./types";
import { AppIcon } from "@/components/app-icon";

type CoinsFeedHeaderProps = {
  stats: StatCard[];
  query: string;
  onQueryChange: (value: string) => void;
  isRefreshing: boolean;
  loadedCount: number;
  newItemsCount: number;
};

export function CoinsFeedHeader({ stats, query, onQueryChange, isRefreshing, loadedCount, newItemsCount }: CoinsFeedHeaderProps) {
  return (
    <section className="overflow-hidden rounded-[24px] border border-[rgba(59,130,246,0.2)] bg-[linear-gradient(180deg,rgba(255,255,255,0.86),rgba(248,250,252,0.92))] text-slate-900 shadow-[0_24px_70px_rgba(15,23,42,0.08)] dark:bg-[linear-gradient(180deg,rgba(15,23,42,0.96),rgba(15,23,42,0.92))] dark:text-slate-100">
      <div className="grid gap-6 px-5 py-5 md:px-6 xl:grid-cols-[minmax(0,1.4fr)_380px] xl:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-primary/10 px-2 py-0.5 text-[11px] font-mono font-bold uppercase tracking-[0.22em] text-primary">
              Live Terminal
            </span>
            <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">v3.0.1-terminal-stable</span>
          </div>
          <h1 className="mt-3 text-3xl font-black uppercase italic tracking-tight text-slate-950 dark:text-slate-100 md:text-[2.6rem]">
            Launch Feed
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-500 dark:text-slate-400">
            Real-time risk assessment engine for newly deployed Solana SPL tokens.
          </p>

          <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="rounded-xl border border-primary/20 bg-primary/5 p-4 dark:border-primary/20 dark:bg-primary/5"
              >
                <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                  {stat.label}
                </span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="font-mono text-2xl font-black tracking-tighter text-primary">{stat.value}</span>
                  <span
                    className={
                      stat.tone === "red"
                        ? "text-xs font-bold text-rose-500"
                        : stat.tone === "orange"
                          ? "text-xs font-bold text-amber-500"
                          : stat.tone === "yellow"
                            ? "text-xs font-bold text-amber-500"
                            : "text-xs font-bold text-primary"
                    }
                  >
                    {stat.detail}
                  </span>
                </div>
                <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-primary/10">
                  <div
                    className={
                      stat.tone === "red"
                        ? "h-full w-[84%] bg-rose-500"
                        : stat.tone === "orange"
                          ? "h-full w-[68%] bg-amber-500"
                          : stat.tone === "yellow"
                            ? "h-full w-[52%] bg-amber-500"
                            : "h-full w-[34%] bg-primary"
                    }
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-primary/20 bg-primary/5 p-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Feed Status</p>
              <p className="mt-2 text-lg font-bold text-slate-950 dark:text-slate-100">
                {isRefreshing ? "Refreshing live feed" : "Auto-refresh active"}
              </p>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                New launches pin to the top automatically on every live sync.
              </p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.12em] text-primary">
                <span className="h-2 w-2 rounded-full bg-primary" />
                LIVE UPDATE
              </span>
              {newItemsCount > 0 ? (
                <span className="rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-400">
                  +{newItemsCount} new token{newItemsCount === 1 ? "" : "s"}
                </span>
              ) : null}
            </div>
          </div>

          <label className="mt-4 flex items-center gap-2 rounded-xl border border-primary/20 bg-background-light px-3 py-3 dark:bg-background-dark/70">
            <AppIcon className="h-5 w-5 text-primary" name="search" />
            <input
              className="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400 dark:text-slate-100"
              onChange={(event) => onQueryChange(event.target.value)}
              placeholder="Search token address..."
              value={query}
            />
          </label>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-primary/20 bg-background-light px-4 py-3 dark:bg-background-dark/60">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">Refresh mode</p>
              <p className="mt-1 text-sm font-semibold text-slate-950 dark:text-slate-100">
                {isRefreshing ? "Syncing latest profiles" : "Passive live refresh"}
              </p>
            </div>
            <div className="rounded-xl border border-primary/20 bg-background-light px-4 py-3 dark:bg-background-dark/60">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">Feed window</p>
              <p className="mt-1 text-sm font-semibold text-slate-950 dark:text-slate-100">{loadedCount} rows loaded</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
