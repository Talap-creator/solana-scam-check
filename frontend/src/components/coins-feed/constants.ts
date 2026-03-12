import type { LaunchFeedTab } from "@/lib/api";
import type { QueryState } from "./types";

export const DEFAULT_QUERY: QueryState = {
  tab: "new",
  sort: "newest",
  age: "all",
  liquidity: "all",
  copycatOnly: false,
  query: "",
};

export const TAB_OPTIONS: Array<{ key: LaunchFeedTab; label: string }> = [
  { key: "new", label: "New" },
  { key: "high-rug", label: "High Rug" },
  { key: "high-caution", label: "High Caution" },
  { key: "coordinated", label: "Coordinated" },
  { key: "copycats", label: "Copycats" },
  { key: "recently-rugged", label: "Recently Rugged" },
];
