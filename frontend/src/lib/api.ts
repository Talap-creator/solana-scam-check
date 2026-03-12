import { type CheckReport } from "@/lib/mock-data";
import { getClientApiBaseUrl, getServerApiBaseUrl } from "@/lib/api-base";

export type WatchlistItem = {
  name: string;
  delta: string;
  state: string;
};

export type AccountWatchlistItem = {
  entity_type: "token" | "wallet" | "project";
  entity_id: string;
  report_id: string | null;
  name: string;
  symbol: string | null;
  delta: string;
  state: string;
  status: "low" | "medium" | "high" | "critical" | null;
  score: number | null;
  refreshed_at: string;
  tracked_at: string;
};

export type ReviewQueueItem = {
  id: string;
  display_name: string;
  entity_type: "token" | "wallet" | "project";
  severity: "low" | "medium" | "high" | "critical";
  score: number;
  owner: string;
  updated_at: string;
};

export type OverviewData = {
  product: string;
  network: string;
  supported_entities: Array<"token" | "wallet" | "project">;
  status_model: Array<"low" | "medium" | "high" | "critical">;
  totals: {
    checks: number;
    watchlist: number;
    review_queue: number;
  };
  freshness: string;
  active_rules: number;
};

export type InsightsData = {
  most_scanned_tokens: Array<{
    token_address: string;
    scan_count: number;
    average_risk_score: number;
  }>;
  trending_rugs: Array<{
    token_address: string;
    risk_score: number;
    confidence: number;
    scan_time: string;
  }>;
};

export type SubmitEntityType = "auto" | "token" | "wallet" | "project";
export type LaunchFeedItem = {
  mint: string;
  report_id: string;
  name: string;
  symbol: string;
  logo_url: string | null;
  age_minutes: number;
  liquidity_usd: number;
  market_cap_usd: number;
  rug_probability: number;
  rug_risk_level: "low" | "medium" | "high" | "critical";
  trade_caution_level: "low" | "moderate" | "high" | "avoid";
  launch_quality: "organic" | "noisy" | "coordinated" | "likely_wash" | "unknown";
  copycat_status: "none" | "possible" | "collision";
  updated_at: string;
  initial_live_estimate: boolean;
  summary: string;
  rug_risk_drivers: string[];
  trade_caution_drivers: string[];
  top_reducer: string | null;
  deployer_short_address: string | null;
};

export type LaunchFeedTab = "new" | "high-rug" | "high-caution" | "coordinated" | "copycats" | "recently-rugged";
export type LaunchFeedSort = "newest" | "highest-rug" | "highest-caution" | "highest-liquidity" | "highest-market-cap";
export type LaunchFeedAge = "all" | "10m" | "1h" | "24h";
export type LaunchFeedLiquidity = "all" | "lt1k" | "1k-5k" | "5k-20k" | "gte20k";

export type LaunchFeedQuery = {
  limit?: number;
  cursor?: string | null;
  tab?: LaunchFeedTab;
  sort?: LaunchFeedSort;
  age?: LaunchFeedAge;
  liquidity?: LaunchFeedLiquidity;
  copycat_only?: boolean;
  q?: string;
};

type ApiReport = {
  id: string;
  entity_type: "token" | "wallet" | "project";
  entity_id: string;
  display_name: string;
  name?: string | null;
  symbol?: string | null;
  logo_url?: string | null;
  status: "low" | "medium" | "high" | "critical";
  score: number;
  rug_probability: number;
  technical_risk: number;
  distribution_risk: number;
  market_execution_risk: number;
  behaviour_risk: number;
  market_maturity: number;
  page_mode?: CheckReport["pageMode"];
  launch_risk?: {
    score: number;
    level: CheckReport["launchRisk"]["level"];
    summary: string;
    drivers: string[];
  };
  early_warnings?: string[];
  launch_radar?: {
    launch_age_minutes: number | null;
    initial_liquidity_band: string;
    early_trade_pressure: CheckReport["launchRadar"]["earlyTradePressure"];
    launch_concentration: CheckReport["launchRadar"]["launchConcentration"];
    copycat_status: CheckReport["launchRadar"]["copycatStatus"];
    early_cluster_activity: CheckReport["launchRadar"]["earlyClusterActivity"];
    summary: string;
  };
  market_source?: string | null;
  confidence: number;
  summary: string;
  refreshed_at: string;
  liquidity: string;
  top_holder_share: string;
  review_state: string;
  risk_breakdown: Array<{
    block: string;
    score: number;
    weight: number;
    weighted_score: number;
    kind?: "risk" | "positive";
  }>;
  factors: CheckReport["factors"];
  risk_increasers?: CheckReport["riskIncreasers"];
  risk_reducers?: CheckReport["riskReducers"];
  behaviour_analysis_v2?: {
    summary: string;
    overall_behaviour_risk: "low" | "medium" | "high" | "critical";
    confidence: "limited" | "medium" | "high";
    score: number;
    modules: Record<
      string,
      {
        key: string;
        title: string;
        status: "clear" | "watch" | "flagged";
        severity: "low" | "medium" | "high";
        score: number;
        summary: string;
        details: string[];
        confidence: "limited" | "medium" | "high";
        evidence: {
          metrics: Record<string, string | number | boolean | null>;
        };
      }
    >;
    confidence_breakdown: {
      holder_coverage: "full" | "partial" | "limited";
      transaction_coverage: "full" | "partial" | "limited";
      funding_trace_depth: "shallow" | "moderate" | "deep";
      liquidity_data: "full" | "partial" | "limited";
    };
    version: string;
  };
  trade_caution?: {
    score: number;
    level: "low" | "moderate" | "high" | "avoid";
    label: string;
    summary: string;
    drivers: string[];
    dimensions: {
      admin_caution: number;
      execution_caution: number;
      concentration_caution: number;
      behavioural_caution: number;
      market_structure_strength: number;
    };
  };
  behaviour_analysis?: CheckReport["behaviourAnalysis"];
  metrics: CheckReport["metrics"];
  timeline: CheckReport["timeline"];
};

type SubmissionResponse = {
  queued: boolean;
  entity_type: "token" | "wallet" | "project";
  requested_value: string;
  check_id: string;
};

export type AuthTokenResponse = {
  access_token: string;
  token_type: "bearer";
};

export type UserProfile = {
  id: string;
  email: string;
  plan: string;
  role: string;
  created_at: string;
  last_login: string | null;
};

export type UserUsage = {
  plan: string;
  used_today: number;
  daily_limit: number;
  remaining_today: number;
  limit_source: "plan" | "custom";
  reset_at: string;
};

export type UserScan = {
  id: string;
  token_address: string;
  risk_score: number;
  confidence: number;
  scan_time: string;
};

export type AdminDashboardData = {
  users_count: number;
  daily_scans: number;
  popular_tokens: Array<{
    token_address: string;
    scan_count: number;
  }>;
  average_risk_score: number;
};

export type AdminUserItem = {
  id: string;
  email: string;
  plan: string;
  custom_daily_scan_limit: number | null;
  effective_daily_limit: number;
  scans: number;
  created_at: string;
};

export type AdminScanItem = {
  id: string;
  user_email: string;
  token_address: string;
  risk_score: number;
  confidence: number;
  scan_time: string;
};

export type AdminTokenItem = {
  token_address: string;
  scan_count: number;
  average_risk_score: number;
  last_scanned: string;
};

export type TokenOverrideVerdict = "whitelist" | "blacklist";

export type AdminTokenOverrideItem = {
  token_address: string;
  chain: string;
  verdict: TokenOverrideVerdict;
  reason: string | null;
  updated_at: string;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function normalizeApiDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object" && "msg" in item && typeof item.msg === "string") {
          return item.msg;
        }
        return null;
      })
      .filter((item): item is string => Boolean(item));

    if (messages.length > 0) {
      return messages.join("; ");
    }
  }

  if (detail && typeof detail === "object") {
    if ("message" in detail && typeof detail.message === "string") {
      return detail.message;
    }
    return JSON.stringify(detail);
  }

  return fallback;
}

function mapReport(report: ApiReport): CheckReport {
  return {
    id: report.id,
    entityType: report.entity_type,
    entityId: report.entity_id,
    displayName: report.display_name,
    name: report.name,
    symbol: report.symbol,
    logoUrl: report.logo_url,
    status: report.status,
    score: report.score,
    rugProbability: report.rug_probability,
    technicalRisk: report.technical_risk,
    distributionRisk: report.distribution_risk,
    marketExecutionRisk: report.market_execution_risk,
    behaviourRisk: report.behaviour_risk,
    marketMaturity: report.market_maturity,
    pageMode: report.page_mode ?? "mature",
    launchRisk: report.launch_risk
      ? {
          score: report.launch_risk.score,
          level: report.launch_risk.level,
          summary: report.launch_risk.summary,
          drivers: report.launch_risk.drivers,
        }
      : {
          score: 0,
          level: "unknown",
          summary: "Launch stage not available.",
          drivers: [],
        },
    earlyWarnings: report.early_warnings ?? [],
    launchRadar: report.launch_radar
      ? {
          launchAgeMinutes: report.launch_radar.launch_age_minutes,
          initialLiquidityBand: report.launch_radar.initial_liquidity_band,
          earlyTradePressure: report.launch_radar.early_trade_pressure,
          launchConcentration: report.launch_radar.launch_concentration,
          copycatStatus: report.launch_radar.copycat_status,
          earlyClusterActivity: report.launch_radar.early_cluster_activity,
          summary: report.launch_radar.summary,
        }
      : {
          launchAgeMinutes: null,
          initialLiquidityBand: "Unknown",
          earlyTradePressure: "balanced",
          launchConcentration: "medium",
          copycatStatus: "none",
          earlyClusterActivity: "none",
          summary: "Launch-stage radar is not available for this report.",
        },
    marketSource: report.market_source,
    tradeCaution: report.trade_caution
      ? {
          score: report.trade_caution.score,
          level: report.trade_caution.level,
          label: report.trade_caution.label,
          summary: report.trade_caution.summary,
          drivers: report.trade_caution.drivers,
          dimensions: {
            adminCaution: report.trade_caution.dimensions.admin_caution,
            executionCaution: report.trade_caution.dimensions.execution_caution,
            concentrationCaution: report.trade_caution.dimensions.concentration_caution,
            behaviouralCaution: report.trade_caution.dimensions.behavioural_caution,
            marketStructureStrength: report.trade_caution.dimensions.market_structure_strength,
          },
        }
      : undefined,
    confidence: report.confidence,
    summary: report.summary,
    refreshedAt: report.refreshed_at,
    liquidity: report.liquidity,
    topHolderShare: report.top_holder_share,
    reviewState: report.review_state,
    riskBreakdown: report.risk_breakdown.map((item) => ({
      block: item.block,
      score: item.score,
      weight: item.weight,
      weightedScore: item.weighted_score,
      kind: item.kind,
    })),
    factors: report.factors,
    riskIncreasers: report.risk_increasers ?? report.factors,
    riskReducers: report.risk_reducers ?? [],
    behaviourAnalysisV2: report.behaviour_analysis_v2
      ? {
          summary: report.behaviour_analysis_v2.summary,
          overallBehaviourRisk: report.behaviour_analysis_v2.overall_behaviour_risk,
          confidence: report.behaviour_analysis_v2.confidence,
          score: report.behaviour_analysis_v2.score,
          modules: Object.fromEntries(
            Object.entries(report.behaviour_analysis_v2.modules).map(([key, module]) => [
              key,
              {
                ...module,
                evidence: module.evidence.metrics,
              },
            ]),
          ),
          confidenceBreakdown: {
            holderCoverage: report.behaviour_analysis_v2.confidence_breakdown.holder_coverage,
            transactionCoverage: report.behaviour_analysis_v2.confidence_breakdown.transaction_coverage,
            fundingTraceDepth: report.behaviour_analysis_v2.confidence_breakdown.funding_trace_depth,
            liquidityData: report.behaviour_analysis_v2.confidence_breakdown.liquidity_data,
          },
          version: report.behaviour_analysis_v2.version,
        }
      : undefined,
    behaviourAnalysis: report.behaviour_analysis ?? [],
    metrics: report.metrics,
    timeline: report.timeline,
  };
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getServerApiBaseUrl()}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = response.statusText;

    try {
      const errorPayload = (await response.json()) as { detail?: unknown };
      if (errorPayload.detail !== undefined) {
        detail = normalizeApiDetail(errorPayload.detail, detail);
      }
    } catch {}

    throw new ApiError(`Request failed: ${detail}`, response.status);
  }

  return response.json() as Promise<T>;
}

export async function getOverview(): Promise<OverviewData> {
  return fetchJson<OverviewData>("/api/v1/overview");
}

export async function getInsights(): Promise<InsightsData> {
  return fetchJson<InsightsData>("/api/v1/insights");
}

export async function getChecks(): Promise<CheckReport[]> {
  const data = await fetchJson<{ items: ApiReport[] }>("/api/v1/checks");
  return data.items.map(mapReport);
}

export async function getCheckById(reportId: string): Promise<CheckReport> {
  const data = await fetchJson<ApiReport>(`/api/v1/checks/${reportId}`);
  return mapReport(data);
}

export async function getWatchlist(): Promise<WatchlistItem[]> {
  const data = await fetchJson<{ items: WatchlistItem[] }>("/api/v1/watchlist");
  return data.items;
}

export async function getAccountWatchlist(): Promise<AccountWatchlistItem[]> {
  const data = await fetchClientAuthed<{ items: AccountWatchlistItem[] }>(
    "/api/v1/auth/watchlist",
    "Unable to load watchlist",
  );
  return data.items;
}

export async function getAccountWatchlistStatus(
  entityType: "token" | "wallet" | "project",
  entityId: string,
): Promise<boolean> {
  const data = await fetchClientAuthed<{ tracked: boolean }>(
    `/api/v1/auth/watchlist/status/${entityType}/${encodeURIComponent(entityId)}`,
    "Unable to load watchlist status",
  );
  return data.tracked;
}

export async function addAccountWatchlistItem(
  entityType: "token" | "wallet" | "project",
  entityId: string,
  displayName?: string,
): Promise<AccountWatchlistItem | null> {
  const data = await fetchClientAuthedWithInit<{ tracked: boolean; item: AccountWatchlistItem | null }>(
    "/api/v1/auth/watchlist",
    {
      method: "POST",
      body: JSON.stringify({
        entity_type: entityType,
        entity_id: entityId,
        display_name: displayName ?? null,
      }),
    },
    "Unable to save watchlist item",
  );
  return data.item;
}

export async function removeAccountWatchlistItem(
  entityType: "token" | "wallet" | "project",
  entityId: string,
): Promise<void> {
  await fetchClientAuthedWithInit<{ tracked: boolean }>(
    `/api/v1/auth/watchlist/${entityType}/${encodeURIComponent(entityId)}`,
    { method: "DELETE" },
    "Unable to remove watchlist item",
  );
}

export async function getReviewQueue(): Promise<ReviewQueueItem[]> {
  const data = await fetchClientAuthed<{ items: ReviewQueueItem[] }>("/api/v1/admin/review-queue");
  return data.items;
}

export async function getLaunchFeed(query: LaunchFeedQuery = {}): Promise<{ items: LaunchFeedItem[]; next_cursor: string | null }> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit ?? 50));

  if (query.cursor) params.set("cursor", query.cursor);
  if (query.tab) params.set("tab", query.tab);
  if (query.sort) params.set("sort", query.sort);
  if (query.age) params.set("age", query.age);
  if (query.liquidity) params.set("liquidity", query.liquidity);
  if (query.copycat_only) params.set("copycat_only", "true");
  if (query.q?.trim()) params.set("q", query.q.trim());

  const baseUrl = typeof window === "undefined" ? getServerApiBaseUrl() : getClientApiBaseUrl();
  const response = await fetch(`${baseUrl}/api/v1/feed/launches?${params.toString()}`, {
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    let detail = response.statusText;

    try {
      const errorPayload = (await response.json()) as { detail?: unknown };
      if (errorPayload.detail !== undefined) {
        detail = normalizeApiDetail(errorPayload.detail, detail);
      }
    } catch {}

    throw new ApiError(`Request failed: ${detail}`, response.status);
  }

  return response.json() as Promise<{ items: LaunchFeedItem[]; next_cursor: string | null }>;
}

function detectEntityType(value: string): Exclude<SubmitEntityType, "auto"> {
  const trimmed = value.trim();

  if (trimmed.startsWith("http://") || trimmed.startsWith("https://") || trimmed.includes(".")) {
    return "project";
  }

  return "token";
}

export function resolveEntityType(value: string, selectedType: SubmitEntityType): Exclude<SubmitEntityType, "auto"> {
  return selectedType === "auto" ? detectEntityType(value) : selectedType;
}

export async function submitCheck(
  value: string,
  selectedType: SubmitEntityType,
): Promise<SubmissionResponse> {
  const entityType = resolveEntityType(value, selectedType);
  const path =
    entityType === "project" ? "/api/v1/check/project" : `/api/v1/check/${entityType}`;
  const body =
    entityType === "project"
      ? JSON.stringify({ query: value.trim() })
      : JSON.stringify({ address: value.trim() });

  const response = await fetch(`${getClientApiBaseUrl()}${path}`, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
    },
    body,
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new ApiError(normalizeApiDetail(payload?.detail, "Unable to submit check"), response.status);
  }

  return response.json() as Promise<SubmissionResponse>;
}

export async function recheckReport(
  entityType: "token" | "wallet" | "project",
  entityId: string,
): Promise<SubmissionResponse> {
  const response = await fetch(
    `${getClientApiBaseUrl()}/api/v1/recheck/${entityType}/${encodeURIComponent(entityId)}`,
    {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
    },
  );

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new ApiError(normalizeApiDetail(payload?.detail, "Unable to recheck report"), response.status);
  }

  return response.json() as Promise<SubmissionResponse>;
}

export async function registerUser(
  email: string,
  password: string,
  plan: "free" | "pro" | "enterprise" = "free",
): Promise<AuthTokenResponse> {
  const response = await fetch(`${getClientApiBaseUrl()}/api/v1/auth/register`, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password, plan }),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new ApiError(normalizeApiDetail(payload?.detail, "Unable to register"), response.status);
  }

  return response.json() as Promise<AuthTokenResponse>;
}

export async function loginUser(email: string, password: string): Promise<AuthTokenResponse> {
  const response = await fetch(`${getClientApiBaseUrl()}/api/v1/auth/login`, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new ApiError(normalizeApiDetail(payload?.detail, "Unable to login"), response.status);
  }

  return response.json() as Promise<AuthTokenResponse>;
}

export async function getMe(): Promise<UserProfile> {
  const response = await fetch(`${getClientApiBaseUrl()}/api/v1/auth/me`, {
    method: "GET",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new ApiError(normalizeApiDetail(payload?.detail, "Unable to fetch profile"), response.status);
  }

  return response.json() as Promise<UserProfile>;
}

export async function getUsage(): Promise<UserUsage> {
  return fetchClientAuthed<UserUsage>("/api/v1/auth/usage");
}

export async function getMyScans(): Promise<UserScan[]> {
  const data = await fetchClientAuthed<{ items: UserScan[] }>("/api/v1/auth/scans");
  return data.items;
}

async function fetchClientAuthed<T>(path: string, fallbackError = "Request failed"): Promise<T> {
  return fetchClientAuthedWithInit<T>(path, { method: "GET" }, fallbackError);
}

async function fetchClientAuthedWithInit<T>(
  path: string,
  init: RequestInit,
  fallbackError = "Request failed",
): Promise<T> {
  const response = await fetch(`${getClientApiBaseUrl()}${path}`, {
    ...init,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new ApiError(normalizeApiDetail(payload?.detail, fallbackError), response.status);
  }

  return response.json() as Promise<T>;
}

export async function getAdminDashboard(): Promise<AdminDashboardData> {
  return fetchClientAuthed<AdminDashboardData>("/api/v1/admin/dashboard");
}

export async function getAdminUsers(): Promise<AdminUserItem[]> {
  const data = await fetchClientAuthed<{ items: AdminUserItem[] }>("/api/v1/admin/users");
  return data.items;
}

export async function updateAdminUserLimits(
  userId: string,
  plan: "free" | "pro" | "enterprise",
  customDailyScanLimit: number | null,
): Promise<AdminUserItem> {
  return fetchClientAuthedWithInit<AdminUserItem>(`/api/v1/admin/users/${encodeURIComponent(userId)}/limits`, {
    method: "PATCH",
    body: JSON.stringify({
      plan,
      custom_daily_scan_limit: customDailyScanLimit,
    }),
  });
}

export async function bulkUpdateAdminUserLimits(
  userIds: string[],
  plan: "free" | "pro" | "enterprise",
  customDailyScanLimit: number | null,
): Promise<{ updated_count: number }> {
  return fetchClientAuthedWithInit<{ updated_count: number }>("/api/v1/admin/users/limits/bulk", {
    method: "PATCH",
    body: JSON.stringify({
      user_ids: userIds,
      plan,
      custom_daily_scan_limit: customDailyScanLimit,
    }),
  });
}

export async function getAdminScans(): Promise<AdminScanItem[]> {
  const data = await fetchClientAuthed<{ items: AdminScanItem[] }>("/api/v1/admin/scans");
  return data.items;
}

export async function getAdminTokens(): Promise<AdminTokenItem[]> {
  const data = await fetchClientAuthed<{ items: AdminTokenItem[] }>("/api/v1/admin/tokens");
  return data.items;
}

export async function getAdminOverrides(): Promise<AdminTokenOverrideItem[]> {
  const data = await fetchClientAuthed<{ items: AdminTokenOverrideItem[] }>("/api/v1/admin/overrides");
  return data.items;
}

export async function upsertAdminOverride(
  token_address: string,
  verdict: TokenOverrideVerdict,
  reason?: string,
): Promise<AdminTokenOverrideItem> {
  return fetchClientAuthedWithInit<AdminTokenOverrideItem>("/api/v1/admin/overrides", {
    method: "POST",
    body: JSON.stringify({
      token_address: token_address.trim(),
      verdict,
      reason: reason?.trim() || null,
    }),
  });
}

export async function deleteAdminOverride(tokenAddress: string): Promise<void> {
  await fetchClientAuthedWithInit<{ deleted: boolean }>(
    `/api/v1/admin/overrides/${encodeURIComponent(tokenAddress)}`,
    { method: "DELETE" },
  );
}

export async function logoutUser(): Promise<void> {
  const response = await fetch(`${getClientApiBaseUrl()}/api/v1/auth/logout`, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new ApiError(normalizeApiDetail(payload?.detail, "Unable to logout"), response.status);
  }
}
