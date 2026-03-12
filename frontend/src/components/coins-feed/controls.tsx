import type { LaunchFeedAge, LaunchFeedLiquidity, LaunchFeedSort } from "@/lib/api";
import { DEFAULT_QUERY, TAB_OPTIONS } from "./constants";
import type { FilterChip, QueryState } from "./types";

type CoinsFeedControlsProps = {
  queryState: QueryState;
  filterChips: FilterChip[];
  onUpdate: (patch: Partial<QueryState>) => void;
};

export function CoinsFeedControls({ queryState, filterChips, onUpdate }: CoinsFeedControlsProps) {
  return (
    <section className="mt-5 space-y-4">
      <div className="flex flex-wrap items-center gap-3 py-1">
        {TAB_OPTIONS.map((item) => {
          const active = queryState.tab === item.key;
          return (
            <button
              key={item.key}
              className={
                active
                  ? "flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-bold uppercase tracking-tight text-slate-50 shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                  : "flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/10 px-4 py-2 text-sm font-bold uppercase tracking-tight text-primary transition hover:bg-primary/20"
              }
              onClick={() => onUpdate({ tab: item.key })}
              type="button"
            >
              {item.label}
            </button>
          );
        })}
        <div className="ml-auto flex items-center gap-2 text-xs font-mono text-slate-500 dark:text-slate-400">
          <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
          LIVE UPDATE
        </div>
      </div>

      <div className="rounded-xl border border-primary/20 bg-background-light/90 p-4 shadow-[0_16px_50px_rgba(15,23,42,0.06)] dark:bg-background-dark/90">
        <div className="grid gap-3 lg:grid-cols-[220px_180px_180px_auto_auto] lg:items-center">
          <select
            className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 text-sm text-slate-900 outline-none dark:text-slate-100"
            onChange={(event) => onUpdate({ sort: event.target.value as LaunchFeedSort })}
            value={queryState.sort}
          >
            <option value="newest">Newest</option>
            <option value="highest-rug">Highest rug risk</option>
            <option value="highest-caution">Highest trade caution</option>
            <option value="highest-liquidity">Highest liquidity</option>
            <option value="highest-market-cap">Highest market cap</option>
          </select>
          <select
            className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 text-sm text-slate-900 outline-none dark:text-slate-100"
            onChange={(event) => onUpdate({ age: event.target.value as LaunchFeedAge })}
            value={queryState.age}
          >
            <option value="all">Age: All</option>
            <option value="10m">&lt; 10m</option>
            <option value="1h">&lt; 1h</option>
            <option value="24h">&lt; 24h</option>
          </select>
          <select
            className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 text-sm text-slate-900 outline-none dark:text-slate-100"
            onChange={(event) => onUpdate({ liquidity: event.target.value as LaunchFeedLiquidity })}
            value={queryState.liquidity}
          >
            <option value="all">Liquidity: All</option>
            <option value="lt1k">&lt; $1k</option>
            <option value="1k-5k">$1k-$5k</option>
            <option value="5k-20k">$5k-$20k</option>
            <option value="gte20k">$20k+</option>
          </select>
          <label className="inline-flex items-center gap-2 rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 text-sm font-medium text-slate-700 dark:text-slate-200">
            <input
              checked={queryState.copycatOnly}
              onChange={() => onUpdate({ copycatOnly: !queryState.copycatOnly })}
              type="checkbox"
            />
            Copycat only
          </label>
          <button
            className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 text-sm font-semibold text-slate-700 dark:text-slate-200"
            onClick={() => onUpdate(DEFAULT_QUERY)}
            type="button"
          >
            Reset
          </button>
        </div>

        {filterChips.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {filterChips.map((chip) => (
              <button
                key={chip.key}
                className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.08em] text-primary"
                onClick={() => onUpdate(chip.clear)}
                type="button"
              >
                {chip.label} x
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
