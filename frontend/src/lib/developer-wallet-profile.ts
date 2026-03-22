import type { CheckReport } from "@/lib/mock-data";

export type DeveloperWalletProfile = {
  status: "clean" | "watch" | "flagged";
  summary: string;
  note: string;
  confidence: string;
  metrics: Array<{ label: string; value: string }>;
  signals: Array<{
    detail: string;
    label: string;
    tone: "neutral" | "watch" | "flagged";
    value: string;
  }>;
  watchpoints: string[];
  coverage: Array<{ label: string; value: string }>;
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

function formatRatioPercent(value: string | number | boolean | null, fallback = "n/a") {
  if (typeof value === "number") {
    return `${(value * 100).toFixed(1)}%`;
  }
  return fallback;
}

function formatDepth(value: string | number | boolean | null, fallback = "n/a") {
  if (typeof value === "number") {
    return `${value.toFixed(1)} hops`;
  }
  return fallback;
}

function scoreTone(
  value: string | number | boolean | null,
  watchThreshold: number,
  flaggedThreshold: number,
): "neutral" | "watch" | "flagged" {
  if (typeof value !== "number") {
    return "neutral";
  }
  if (value >= flaggedThreshold) {
    return "flagged";
  }
  if (value >= watchThreshold) {
    return "watch";
  }
  return "neutral";
}

function titleCase(value: string) {
  return value
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function deriveDeveloperWalletProfile(report: CheckReport): DeveloperWalletProfile | null {
  if (report.entityType !== "token") {
    return null;
  }

  const modules = report.behaviourAnalysisV2?.modules;
  const developer = modules?.developer_cluster;
  const earlyBuyers = modules?.early_buyers;
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
      signals: [
        {
          detail: "Current report does not contain enough holder-graph evidence to infer linked-wallet control.",
          label: "Shared funding coverage",
          tone: "neutral",
          value: "n/a",
        },
        {
          detail: "No deployer-adjacent exit density was confirmed from the current evidence window.",
          label: "Exit wallet density",
          tone: "neutral",
          value: "n/a",
        },
      ],
      watchpoints: ["No strong developer-adjacent coordination signal is active right now."],
      coverage: [
        { label: "Holder coverage", value: "Limited" },
        { label: "Funding trace depth", value: "Shallow" },
      ],
    };
  }

  const developerMetrics = developer?.evidence ?? {};
  const earlyBuyerMetrics = earlyBuyers?.evidence ?? {};
  const insiderMetrics = insider?.evidence ?? {};
  const linkedWallets = readMetric(
    developerMetrics,
    "estimated_cluster_wallet_count",
    "shared_funding_wallet_count",
    "top_wallets_with_common_funder_count",
  );
  const clusterSupply = readMetric(
    developerMetrics,
    "estimated_cluster_supply_share",
    "cluster_supply_control_pct",
  );
  const fundingRatio = readMetric(developerMetrics, "shared_funding_ratio");
  const sellerWallets = readMetric(insiderMetrics, "top_holder_exit_density", "seller_wallet_count");
  const exitSimilarity = readMetric(
    insiderMetrics,
    "wallet_exit_similarity_score",
    "coordinated_exit_window_score",
  );
  const sellBeforeLiquidityDrop = readMetric(insiderMetrics, "sell_before_liquidity_drop_score");
  const sharedFunder = readMetric(developerMetrics, "shared_funder");
  const directTransfers = readMetric(
    developerMetrics,
    "direct_token_transfer_between_top_wallets",
    "direct_wallet_overlap_count",
  );
  const sharedOutgoing = readMetric(developerMetrics, "shared_outgoing_wallets_count");
  const multiHopFunders = readMetric(
    developerMetrics,
    "multi_hop_shared_funder_count",
    "multi_hop_shared_funder_count",
  );
  const traceDepth = readMetric(
    developerMetrics,
    "cluster_funding_depth_avg",
    "funding_trace_depth_avg",
  );
  const timingSimilarity = readMetric(
    developerMetrics,
    "holder_activity_time_similarity_score",
    "same_window_buy_density",
  );
  const overlapWithDevCluster = readMetric(earlyBuyerMetrics, "overlap_with_dev_cluster");
  const overlapWithTopHolders = readMetric(earlyBuyerMetrics, "overlap_with_top_holders");

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
  const watchpoints = [
    typeof sharedFunder === "string" && sharedFunder.length > 8
      ? `A shared funding route points back to ${sharedFunder.slice(0, 4)}...${sharedFunder.slice(-4)}.`
      : null,
    typeof fundingRatio === "number" && fundingRatio >= 0.34
      ? "A meaningful share of tracked holder wallets map back into the same funding network."
      : null,
    typeof clusterSupply === "number" && clusterSupply >= 12
      ? "Linked holder wallets control a noticeable share of the tracked supply."
      : null,
    typeof sellerWallets === "number" && sellerWallets >= 2
      ? "Multiple tracked large-holder wallets are contributing to current exit pressure."
      : null,
    typeof exitSimilarity === "number" && exitSimilarity >= 0.45
      ? "Seller timing is compressed into a narrow exit window instead of looking organic."
      : null,
    typeof overlapWithDevCluster === "number" && overlapWithDevCluster >= 0.25
      ? "Early-buyer overlap with the developer-linked cluster is elevated."
      : null,
  ].filter((item): item is string => Boolean(item));

  const confidenceBreakdown = report.behaviourAnalysisV2?.confidenceBreakdown;
  const coverage = confidenceBreakdown
    ? [
        { label: "Holder coverage", value: titleCase(confidenceBreakdown.holderCoverage) },
        { label: "Transaction coverage", value: titleCase(confidenceBreakdown.transactionCoverage) },
        { label: "Funding trace depth", value: titleCase(confidenceBreakdown.fundingTraceDepth) },
        { label: "Liquidity data", value: titleCase(confidenceBreakdown.liquidityData) },
      ]
    : [
        { label: "Holder coverage", value: "Limited" },
        { label: "Funding trace depth", value: "Shallow" },
      ];

  return {
    status,
    summary,
    note,
    confidence: confidenceLabel(developer?.confidence ?? insider?.confidence ?? report.behaviourAnalysisV2?.confidence),
    metrics: [
      { label: "Linked wallets", value: formatCount(linkedWallets) },
      { label: "Cluster supply", value: formatPercent(clusterSupply) },
      { label: "Seller wallets", value: formatCount(sellerWallets) },
      { label: "Funding overlap", value: formatRatioPercent(fundingRatio) },
    ],
    signals: [
      {
        detail: "How much of the tracked holder set resolves back into the same funding graph.",
        label: "Shared funding coverage",
        tone: scoreTone(typeof fundingRatio === "number" ? fundingRatio * 100 : null, 34, 55),
        value: formatRatioPercent(fundingRatio),
      },
      {
        detail: "Estimated share of tracked supply controlled by wallets inside the linked cluster.",
        label: "Cluster supply control",
        tone: scoreTone(clusterSupply, 12, 24),
        value: formatPercent(clusterSupply),
      },
      {
        detail: "Tracked holder wallets transferring directly between each other instead of routing independently.",
        label: "Direct transfer overlap",
        tone: scoreTone(directTransfers, 1, 2),
        value: formatCount(directTransfers, "n/a"),
      },
      {
        detail: "Large-holder exits now visible across the current launch footprint.",
        label: "Exit wallet density",
        tone: scoreTone(sellerWallets, 2, 3),
        value: formatCount(sellerWallets, "n/a"),
      },
      {
        detail: "How tightly seller timing compresses into the same exit window.",
        label: "Exit timing compression",
        tone: scoreTone(typeof exitSimilarity === "number" ? exitSimilarity * 100 : null, 40, 65),
        value: formatRatioPercent(exitSimilarity),
      },
      {
        detail: "How deep the current funding graph can be followed before the trace breaks.",
        label: "Funding trace depth",
        tone: scoreTone(traceDepth, 1.2, 1.8),
        value: formatDepth(traceDepth),
      },
      {
        detail: "Holder wallets sending funds into the same destinations after acquisition.",
        label: "Shared outgoing routes",
        tone: scoreTone(sharedOutgoing, 1, 2),
        value: formatCount(sharedOutgoing, "n/a"),
      },
      {
        detail: "How much the earliest buyer cluster overlaps with wallets already linked to the deployer cluster.",
        label: "Early-buyer overlap",
        tone: scoreTone(typeof overlapWithDevCluster === "number" ? overlapWithDevCluster * 100 : null, 20, 40),
        value: formatRatioPercent(overlapWithDevCluster, formatRatioPercent(overlapWithTopHolders)),
      },
      {
        detail: "Distinct multi-hop funder routes that still collapse back into the same origin graph.",
        label: "Multi-hop funders",
        tone: scoreTone(multiHopFunders, 1, 2),
        value: formatCount(multiHopFunders, "n/a"),
      },
      {
        detail: "Timing similarity across tracked holder activity inside the linked cluster.",
        label: "Activity timing similarity",
        tone: scoreTone(typeof timingSimilarity === "number" ? timingSimilarity * 100 : null, 35, 60),
        value: formatRatioPercent(timingSimilarity),
      },
      {
        detail: "Signals that current exits are happening before liquidity weakens.",
        label: "Sell-before-drop signal",
        tone: scoreTone(typeof sellBeforeLiquidityDrop === "number" ? sellBeforeLiquidityDrop * 100 : null, 50, 90),
        value: formatRatioPercent(sellBeforeLiquidityDrop),
      },
    ],
    watchpoints: watchpoints.length
      ? watchpoints
      : ["No strong developer-adjacent coordination signal is active right now."],
    coverage,
  };
}
