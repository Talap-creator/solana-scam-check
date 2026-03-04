import { dashboardHistory, featuredReport, type CheckReport } from "@/lib/mock-data";

type WatchlistItem = {
  name: string;
  delta: string;
  state: string;
};

type ReviewQueueItem = {
  id: string;
  display_name: string;
  entity_type: string;
  severity: string;
  score: number;
  owner: string;
  updated_at: string;
};

const API_BASE_URL = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

function mapReport(report: {
  id: string;
  entity_type: "token" | "wallet" | "project";
  entity_id: string;
  display_name: string;
  status: "low" | "medium" | "high" | "critical";
  score: number;
  confidence: number;
  summary: string;
  refreshed_at: string;
  liquidity: string;
  top_holder_share: string;
  review_state: string;
  factors: CheckReport["factors"];
  metrics: CheckReport["metrics"];
  timeline: CheckReport["timeline"];
}): CheckReport {
  return {
    id: report.id,
    entityType: report.entity_type,
    entityId: report.entity_id,
    displayName: report.display_name,
    status: report.status,
    score: report.score,
    confidence: report.confidence,
    summary: report.summary,
    refreshedAt: report.refreshed_at,
    liquidity: report.liquidity,
    topHolderShare: report.top_holder_share,
    reviewState: report.review_state,
    factors: report.factors,
    metrics: report.metrics,
    timeline: report.timeline,
  };
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export async function getChecks(): Promise<CheckReport[]> {
  try {
    const data = await fetchJson<{ items: Array<Parameters<typeof mapReport>[0]> }>("/api/v1/checks");
    return data.items.map(mapReport);
  } catch {
    return dashboardHistory;
  }
}

export async function getCheckById(reportId: string): Promise<CheckReport> {
  try {
    const data = await fetchJson<Parameters<typeof mapReport>[0]>(`/api/v1/checks/${reportId}`);
    return mapReport(data);
  } catch {
    return dashboardHistory.find((item) => item.id === reportId) ?? featuredReport;
  }
}

export async function getWatchlist(): Promise<WatchlistItem[]> {
  try {
    const data = await fetchJson<{ items: WatchlistItem[] }>("/api/v1/watchlist");
    return data.items;
  } catch {
    return [
      { name: "PEARL", delta: "+12 score", state: "Critical" },
      { name: "Orbit Project", delta: "confidence down", state: "Watch" },
      { name: "Wallet / 8PX1", delta: "new flagged link", state: "Queued" },
    ];
  }
}

export async function getReviewQueue(): Promise<ReviewQueueItem[]> {
  try {
    const data = await fetchJson<{ items: ReviewQueueItem[] }>("/api/v1/admin/review-queue");
    return data.items;
  } catch {
    return [
      {
        id: "pearl-token",
        display_name: "PEARL / Solana meme token",
        entity_type: "token",
        severity: "critical",
        score: 82,
        owner: "talap",
        updated_at: "4 минуты назад",
      },
    ];
  }
}
