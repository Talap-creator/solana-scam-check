import { deriveDeveloperWalletProfile } from "@/lib/developer-wallet-profile";
import { deriveLaunchPatternFromReport, launchPatternLabel } from "@/lib/launch-pattern";
import type { CheckReport } from "@/lib/mock-data";

export type DeveloperLeadProfile = {
  avgRugProbability: number;
  avgTradeCaution: string;
  confidence: string;
  flags: string[];
  id: string;
  kind: "cluster" | "wallet";
  label: string;
  latestLaunches: Array<{
    id: string;
    launchPattern: string | null;
    name: string;
    pageMode: CheckReport["pageMode"];
    risk: CheckReport["status"];
    symbol: string;
  }>;
  launches: number;
  premiumPrompt: string;
  summary: string;
  unresolved: boolean;
  walletPreview: string;
};

function shortAddress(value: string) {
  return `${value.slice(0, 4)}...${value.slice(-4)}`;
}

function confidenceLabel(value: number) {
  if (value >= 0.75) return "High confidence";
  if (value >= 0.45) return "Moderate confidence";
  return "Limited early data";
}

function avgTradeCautionLabel(levels: string[]) {
  if (levels.includes("avoid")) return "Avoid";
  if (levels.includes("high")) return "High caution";
  if (levels.includes("moderate")) return "Moderate caution";
  return "Low caution";
}

function toneCount(reports: CheckReport[], status: CheckReport["status"]) {
  return reports.filter((item) => item.status === status).length;
}

function makeClusterKey(report: CheckReport) {
  return `cluster:${report.id}`;
}

export function deriveDeveloperLeadProfiles(reports: CheckReport[]): DeveloperLeadProfile[] {
  const tokenReports = reports.filter((report) => report.entityType === "token");
  const orderMap = new Map<string, number>();
  tokenReports.forEach((report, index) => {
    orderMap.set(report.id, index);
  });
  const grouped = new Map<string, CheckReport[]>();
  const walletLabels = new Map<string, { kind: "cluster" | "wallet"; label: string; preview: string; unresolved: boolean }>();

  for (const report of tokenReports) {
    const developerMetrics = report.behaviourAnalysisV2?.modules?.developer_cluster?.evidence ?? {};
    const sharedFunder = developerMetrics.shared_funder;
    const key = typeof sharedFunder === "string" && sharedFunder.length > 8 ? sharedFunder : makeClusterKey(report);
    const entry = grouped.get(key) ?? [];
    entry.push(report);
    grouped.set(key, entry);

    if (!walletLabels.has(key)) {
      if (typeof sharedFunder === "string" && sharedFunder.length > 8) {
        walletLabels.set(key, {
          kind: "wallet",
          label: shortAddress(sharedFunder),
          preview: sharedFunder,
          unresolved: false,
        });
      } else {
        walletLabels.set(key, {
          kind: "cluster",
          label: `Signal Cluster ${report.symbol ?? report.displayName.slice(0, 4).toUpperCase()}`,
          preview: "Wallet hidden",
          unresolved: true,
        });
      }
    }
  }

  return Array.from(grouped.entries())
    .map(([key, items]) => {
      const ordered = [...items].sort(
        (a, b) => (orderMap.get(a.id) ?? Number.MAX_SAFE_INTEGER) - (orderMap.get(b.id) ?? Number.MAX_SAFE_INTEGER),
      );
      const latest = ordered[0];
      const profile = deriveDeveloperWalletProfile(latest);
      const flags = [
        ...(profile?.watchpoints ?? []),
        ...ordered.flatMap((item) => item.riskIncreasers.slice(0, 2).map((factor) => factor.label)),
      ];
      const launchCount = ordered.length;
      const avgRugProbability =
        ordered.reduce((total, item) => total + item.rugProbability, 0) / Math.max(launchCount, 1);
      const cautionLevels = ordered
        .map((item) => item.tradeCaution?.level ?? "moderate")
        .filter((item): item is "low" | "moderate" | "high" | "avoid" => Boolean(item));
      const criticalCount = toneCount(ordered, "critical");
      const highCount = toneCount(ordered, "high");
      const meta = walletLabels.get(key)!;
      return {
        id: key,
        kind: meta.kind,
        label: meta.label,
        walletPreview: meta.preview,
        unresolved: meta.unresolved,
        launches: launchCount,
        avgRugProbability: Math.round(avgRugProbability),
        avgTradeCaution: avgTradeCautionLabel(cautionLevels),
        confidence: confidenceLabel(latest.confidence),
        summary:
          meta.kind === "wallet"
            ? profile?.summary ??
              `This launch wallet has ${launchCount} tracked launch${launchCount === 1 ? "" : "es"} with ${criticalCount + highCount} high-risk outcomes.`
            : profile?.summary ??
              "We see a meaningful connected-wallet pattern, but the exact upstream launch wallet is still hidden behind the current funding graph.",
        flags: Array.from(new Set(flags)).slice(0, 4),
        latestLaunches: ordered.slice(0, 4).map((item) => ({
          id: item.id,
          name: item.name ?? item.displayName,
          symbol: item.symbol ?? item.displayName.slice(0, 5).toUpperCase(),
          risk: item.status,
          pageMode: item.pageMode,
          launchPattern: (() => {
            const pattern = deriveLaunchPatternFromReport(item);
            return pattern ? launchPatternLabel(pattern) : null;
          })(),
        })),
        premiumPrompt:
          meta.kind === "wallet"
            ? "Want to unlock this launch wallet, its full history, and linked launches? Write Mr Talap."
            : "Want to reveal the wallet behind this launch cluster and its full launch history? Write Mr Talap.",
      };
    })
    .sort((left, right) => {
      if (left.kind !== right.kind) {
        return left.kind === "wallet" ? -1 : 1;
      }
      if (right.launches !== left.launches) {
        return right.launches - left.launches;
      }
      return right.avgRugProbability - left.avgRugProbability;
    });
}
