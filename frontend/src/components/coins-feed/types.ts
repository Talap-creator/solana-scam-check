import type { LaunchFeedAge, LaunchFeedLiquidity, LaunchFeedSort, LaunchFeedTab } from "@/lib/api";

export type CoinsFeedProps = {
  initialSearchParams?: Record<string, string | string[] | undefined>;
};

export type QueryState = {
  tab: LaunchFeedTab;
  sort: LaunchFeedSort;
  age: LaunchFeedAge;
  liquidity: LaunchFeedLiquidity;
  copycatOnly: boolean;
  query: string;
};

export type Tone = "green" | "yellow" | "orange" | "red" | "neutral";

export type StatCard = {
  label: string;
  value: string;
  tone: Tone;
  detail: string;
};

export type FilterChip = {
  key: string;
  label: string;
  clear: Partial<QueryState>;
};
