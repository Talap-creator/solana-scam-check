import type { LaunchFeedItem } from "@/lib/api";
import { DEFAULT_QUERY, TAB_OPTIONS } from "./constants";
import type { FilterChip, QueryState, StatCard, Tone } from "./types";

export function parseSingle(value: string | string[] | undefined): string | undefined {
  if (Array.isArray(value)) return value[0];
  return value;
}

export function normalizeQueryState(raw?: Record<string, string | string[] | undefined>): QueryState {
  const tab = parseSingle(raw?.tab);
  const sort = parseSingle(raw?.sort);
  const age = parseSingle(raw?.age);
  const liquidity = parseSingle(raw?.liquidity);
  const query = parseSingle(raw?.q);
  const copycatOnly = parseSingle(raw?.copycat_only);

  return {
    tab: TAB_OPTIONS.some((item) => item.key === tab) ? (tab as QueryState["tab"]) : DEFAULT_QUERY.tab,
    sort:
      sort && ["newest", "highest-rug", "highest-caution", "highest-liquidity", "highest-market-cap"].includes(sort)
        ? (sort as QueryState["sort"])
        : DEFAULT_QUERY.sort,
    age: age && ["all", "10m", "1h", "24h"].includes(age) ? (age as QueryState["age"]) : DEFAULT_QUERY.age,
    liquidity:
      liquidity && ["all", "lt1k", "1k-5k", "5k-20k", "gte20k"].includes(liquidity)
        ? (liquidity as QueryState["liquidity"])
        : DEFAULT_QUERY.liquidity,
    copycatOnly: copycatOnly === "true",
    query: query ?? "",
  };
}

export function buildSearchParams(state: QueryState): URLSearchParams {
  const params = new URLSearchParams();
  if (state.tab !== DEFAULT_QUERY.tab) params.set("tab", state.tab);
  if (state.sort !== DEFAULT_QUERY.sort) params.set("sort", state.sort);
  if (state.age !== DEFAULT_QUERY.age) params.set("age", state.age);
  if (state.liquidity !== DEFAULT_QUERY.liquidity) params.set("liquidity", state.liquidity);
  if (state.copycatOnly) params.set("copycat_only", "true");
  if (state.query.trim()) params.set("q", state.query.trim());
  return params;
}

export function formatMoney(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(2)}K`;
  return `$${value.toFixed(0)}`;
}

export function formatAge(ageMinutes: number): string {
  if (ageMinutes < 60) return `${ageMinutes}m`;
  if (ageMinutes < 1440) return `${Math.floor(ageMinutes / 60)}h`;
  return `${Math.floor(ageMinutes / 1440)}d`;
}

export function formatUpdated(timestamp: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(timestamp));
}

function updatedAtValue(value: string): number {
  const timestamp = Date.parse(value);
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

export function sortLaunchFeedItems(items: LaunchFeedItem[]): LaunchFeedItem[] {
  return [...items].sort((left, right) => {
    if (left.age_minutes !== right.age_minutes) {
      return left.age_minutes - right.age_minutes;
    }

    return updatedAtValue(right.updated_at) - updatedAtValue(left.updated_at);
  });
}

export function mergeLaunchFeedItems(
  current: LaunchFeedItem[],
  incoming: LaunchFeedItem[],
): LaunchFeedItem[] {
  const merged = new Map<string, LaunchFeedItem>();

  for (const item of current) {
    merged.set(item.mint, item);
  }

  for (const item of incoming) {
    merged.set(item.mint, item);
  }

  return sortLaunchFeedItems(Array.from(merged.values()));
}

export function badgeClass(tone: Tone): string {
  if (tone === "green") return "border-[rgba(143,255,168,0.25)] bg-[rgba(143,255,168,0.12)] text-[var(--accent-deep)]";
  if (tone === "yellow") return "border-[rgba(255,213,102,0.25)] bg-[rgba(255,213,102,0.12)] text-[#ffd566]";
  if (tone === "orange") return "border-[rgba(255,159,107,0.25)] bg-[rgba(255,159,107,0.12)] text-[#ff9f6b]";
  if (tone === "red") return "border-[rgba(255,123,120,0.28)] bg-[linear-gradient(135deg,rgba(154,43,57,0.8),rgba(255,123,120,0.26))] text-white";
  return "border-[color:var(--border)] bg-white/6 text-[var(--muted)]";
}

export function rugTone(level: LaunchFeedItem["rug_risk_level"]): Tone {
  if (level === "critical") return "red";
  if (level === "high") return "orange";
  if (level === "medium") return "yellow";
  return "green";
}

export function cautionTone(level: LaunchFeedItem["trade_caution_level"]): Tone {
  if (level === "avoid") return "red";
  if (level === "high") return "orange";
  if (level === "moderate") return "yellow";
  return "neutral";
}

export function launchTone(level: LaunchFeedItem["launch_quality"]): Tone {
  if (level === "likely_wash") return "red";
  if (level === "coordinated") return "orange";
  if (level === "noisy") return "yellow";
  if (level === "organic") return "green";
  return "neutral";
}

export function copycatTone(level: LaunchFeedItem["copycat_status"]): Tone {
  if (level === "collision") return "orange";
  if (level === "possible") return "yellow";
  return "neutral";
}

export function tradeCautionLabel(level: LaunchFeedItem["trade_caution_level"]): string {
  return {
    low: "Low caution",
    moderate: "Moderate caution",
    high: "High caution",
    avoid: "Avoid",
  }[level];
}

export function launchQualityLabel(level: LaunchFeedItem["launch_quality"]): string {
  return {
    organic: "Organic",
    noisy: "Noisy",
    coordinated: "Coordinated",
    likely_wash: "Likely Wash",
    unknown: "Not enough data",
  }[level];
}

export function copycatLabel(level: LaunchFeedItem["copycat_status"]): string {
  return {
    none: "None",
    possible: "Possible copycat",
    collision: "Name collision",
  }[level];
}

export function buildStats(items: LaunchFeedItem[]): StatCard[] {
  const highRug = items.filter((item) => ["high", "critical"].includes(item.rug_risk_level)).length;
  const avoid = items.filter((item) => item.trade_caution_level === "avoid").length;
  const initial = items.filter((item) => item.initial_live_estimate).length;

  return [
    { label: "Tracked launches", value: String(items.length), tone: "neutral", detail: "Current feed window" },
    {
      label: "High rug signals",
      value: String(highRug),
      tone: highRug > 0 ? "orange" : "green",
      detail: "High or critical rows",
    },
    {
      label: "Avoid setups",
      value: String(avoid),
      tone: avoid > 0 ? "red" : "green",
      detail: "Extreme trade caution",
    },
    {
      label: "Initial estimates",
      value: String(initial),
      tone: initial > 0 ? "yellow" : "neutral",
      detail: "Lightweight live rows",
    },
  ];
}

export function buildFilterChips(state: QueryState): FilterChip[] {
  const chips: FilterChip[] = [];
  if (state.age !== "all") chips.push({ key: "age", label: `Age: ${state.age}`, clear: { age: "all" } });
  if (state.liquidity !== "all") chips.push({ key: "liquidity", label: `Liquidity: ${state.liquidity}`, clear: { liquidity: "all" } });
  if (state.copycatOnly) chips.push({ key: "copycat", label: "Copycat only", clear: { copycatOnly: false } });
  if (state.query.trim()) chips.push({ key: "query", label: `Search: ${state.query.trim()}`, clear: { query: "" } });
  return chips;
}

export function summaryFallback(item: LaunchFeedItem): string {
  if (item.rug_risk_level === "low" && ["high", "avoid"].includes(item.trade_caution_level)) {
    return "Low rug probability, but trading conditions remain unfavorable.";
  }
  return item.summary;
}
