import type { CheckReport } from "@/lib/mock-data";

export type WalletIntelligenceProfile = {
  metrics: Array<{ label: string; value: string }>;
  note: string;
  persona: string;
  signals: Array<{ detail: string; label: string }>;
  status: "clean" | "watch" | "flagged";
  summary: string;
  watchpoints: string[];
};

function readMetric(report: CheckReport, ...labels: string[]) {
  for (const label of labels) {
    const metric = report.metrics.find((item) => item.label.toLowerCase() === label.toLowerCase());
    if (metric?.value) {
      return metric.value;
    }
  }
  return "n/a";
}

function derivePersona(report: CheckReport) {
  const codes = new Set(report.factors.map((factor) => factor.code));

  if (codes.has("WALLET_LINKED_FLAGGED") && codes.has("WALLET_LAUNCH_DUMP")) {
    return "Networked launch flipper";
  }
  if (codes.has("WALLET_LINKED_FLAGGED") && codes.has("WALLET_DEPLOYER_HISTORY")) {
    return "Networked repeat deployer";
  }
  if (codes.has("WALLET_LAUNCH_DUMP")) {
    return "Momentum exit wallet";
  }
  if (codes.has("WALLET_DEPLOYER_HISTORY")) {
    return "Repeat deployer wallet";
  }
  return "Low-signal wallet";
}

export function deriveWalletIntelligenceProfile(report: CheckReport): WalletIntelligenceProfile | null {
  if (report.entityType !== "wallet") {
    return null;
  }

  const status =
    report.status === "critical" || report.status === "high"
      ? "flagged"
      : report.status === "medium"
        ? "watch"
        : "clean";

  return {
    status,
    persona: derivePersona(report),
    summary:
      status === "flagged"
        ? "This wallet already shows the kind of connected-risk and exit behaviour that usually takes multiple explorer tabs and historical launch review to confirm manually."
        : status === "watch"
          ? "This wallet is not clean enough for blind copy-trading. Some linked-risk or launch-exit signals are present, but the pattern is not yet severe."
          : "This wallet does not currently show a strong linked-risk or serial-exit footprint in the available evidence window.",
    note:
      "Wallet intelligence compresses linked flags, launch-dump behaviour, deployer history, and review coverage into one operator-facing view.",
    metrics: [
      { label: "Linked flags", value: readMetric(report, "Linked flags") },
      { label: "Active days", value: readMetric(report, "Active days") },
      { label: "Behaviour risk", value: `${report.behaviourRisk}/100` },
      { label: "Review state", value: report.reviewState },
    ],
    signals: [
      {
        label: "Launch-dump streak",
        detail:
          report.factors.find((factor) => factor.code === "WALLET_LAUNCH_DUMP")?.explanation ??
          "No strong repeated launch-entry and rapid-exit streak is visible right now.",
      },
      {
        label: "Linked risky counterparties",
        detail:
          report.factors.find((factor) => factor.code === "WALLET_LINKED_FLAGGED")?.explanation ??
          "Counterparty overlap with already-flagged wallets is not a dominant signal in this report.",
      },
      {
        label: "Deployer history",
        detail:
          report.factors.find((factor) => factor.code === "WALLET_DEPLOYER_HISTORY")?.explanation ??
          "No heavy repeat-deployer footprint is dominating this wallet read yet.",
      },
      {
        label: "Execution caution",
        detail:
          report.marketExecutionRisk >= 55
            ? "Execution-side risk is elevated, so copying this wallet into fresh launches can produce worse entries and exits than the wallet itself achieved."
            : "Execution-side conditions are not the main problem; the wallet-level behaviour is the bigger read.",
      },
    ],
    watchpoints:
      report.factors.length > 0
        ? report.factors.slice(0, 3).map((factor) => factor.label)
        : ["No strong wallet-specific watchpoint is active right now."],
  };
}
