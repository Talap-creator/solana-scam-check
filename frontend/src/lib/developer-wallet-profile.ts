import type { CheckReport } from "@/lib/mock-data";

export type DeveloperWalletProfile = {
  status: "clean" | "watch" | "flagged";
  summary: string;
  note: string;
  confidence: string;
  metrics: Array<{ label: string; value: string }>;
};

function readMetric(
  metrics: Record<string, string | number | boolean | null>,
  ...keys: string[]
): string | number | boolean | null {
  for (const key of keys) {
    if (key in metrics) {
      return metrics[key] ?? null;
    }
  }
  return null;
}

function formatPercent(value: string | number | boolean | null, fallback = "n/a") {
  if (typeof value === "number") {
    return `${value.toFixed(1)}%`;
  }
  return fallback;
}

function formatCount(value: string | number | boolean | null, fallback = "0") {
  if (typeof value === "number") {
    return String(Math.round(value));
  }
  return fallback;
}

function confidenceLabel(value: "limited" | "medium" | "high" | undefined) {
  if (value === "high") return "High confidence";
  if (value === "medium") return "Moderate confidence";
  return "Limited early data";
}

export function deriveDeveloperWalletProfile(report: CheckReport): DeveloperWalletProfile | null {
  if (report.entityType !== "token") {
    return null;
  }

  const modules = report.behaviourAnalysisV2?.modules;
  const developer = modules?.developer_cluster;
  const insider = modules?.insider_selling;

  if (!developer && !insider) {
    return {
      status: "clean",
      summary: "No strong developer-linked wallet cluster was inferred from current holder and funding overlap data.",
      note: "Developer wallet profiling is limited for this token because cluster evidence is still sparse.",
      confidence: confidenceLabel(report.behaviourAnalysisV2?.confidence),
      metrics: [
        { label: "Linked wallets", value: "0" },
        { label: "Cluster supply", value: "n/a" },
        { label: "Seller wallets", value: "0" },
        { label: "Funding overlap", value: "n/a" },
      ],
    };
  }

  const developerMetrics = developer?.evidence ?? {};
  const insiderMetrics = insider?.evidence ?? {};
  const linkedWallets = readMetric(
    developerMetrics,
    "estimated_cluster_wallet_count",
    "shared_funding_wallet_count",
    "top_wallets_with_common_funder_count",
  );
  const clusterSupply = readMetric(developerMetrics, "cluster_supply_control_pct");
  const fundingRatio = readMetric(developerMetrics, "shared_funding_ratio");
  const sellerWallets = readMetric(insiderMetrics, "seller_wallet_count");
  const sellerSupply = readMetric(insiderMetrics, "seller_supply_control_pct");

  const status =
    developer?.status === "flagged" || insider?.status === "flagged"
      ? "flagged"
      : developer?.status === "watch" || insider?.status === "watch"
        ? "watch"
        : "clean";

  const summary =
    status === "flagged"
      ? "Developer-linked or insider-style wallet coordination is elevated and should be treated as a material launch risk."
      : status === "watch"
        ? "Some developer-linked wallet overlap is present, but the cluster is not yet strong enough for a hard insider verdict."
        : "Current developer wallet profile does not show a strong linked-wallet control pattern.";

  const note = developer?.summary ?? insider?.summary ?? "Developer wallet evidence is still forming for this launch.";

  return {
    status,
    summary,
    note,
    confidence: confidenceLabel(developer?.confidence ?? insider?.confidence ?? report.behaviourAnalysisV2?.confidence),
    metrics: [
      { label: "Linked wallets", value: formatCount(linkedWallets) },
      { label: "Cluster supply", value: formatPercent(clusterSupply) },
      { label: "Seller wallets", value: formatCount(sellerWallets) },
      {
        label: "Funding overlap",
        value: typeof fundingRatio === "number" ? `${(fundingRatio * 100).toFixed(1)}%` : formatPercent(sellerSupply),
      },
    ],
  };
}
