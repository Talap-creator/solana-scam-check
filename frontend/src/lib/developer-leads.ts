import { deriveDeveloperWalletProfile } from "@/lib/developer-wallet-profile";
import { deriveLaunchPatternFromReport, launchPatternLabel } from "@/lib/launch-pattern";
import type { CheckReport } from "@/lib/mock-data";

export type DeveloperLeadProfile = {
  avgRugProbability: number;
  avgTradeCaution: string;
  confidence: string;
  coverage: string;
  flags: string[];
  fundingSource: string | null;
  highRiskLaunches: number;
  id: string;
  kind: "cluster" | "wallet";
  label: string;
  latestLaunches: Array<{
    ageMinutes: number | null;
    id: string;
    launchPattern: string | null;
    name: string;
    pageMode: CheckReport["pageMode"];
    refreshedAt: string;
    risk: CheckReport["status"];
    symbol: string;
  }>;
  latestRefreshedAt: string;
  launches: number;
  operatorScore: number;
  premiumPrompt: string;
  profileSignals: Array<{
    label: string;
    tone: "neutral" | "watch" | "flagged";
    value: string;
  }>;
  profileStatus: "clean" | "watch" | "flagged";
  riskyLaunchRatio: number;
  summary: string;
  topMetrics: Array<{ label: string; value: string }>;
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

function cautionWeight(level: string) {
  if (/avoid/i.test(level)) return 16;
  if (/high/i.test(level)) return 11;
  if (/moderate/i.test(level)) return 6;
  return 2;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function reportTimestamp(report: CheckReport, orderMap: Map<string, number>) {
  const parsed = Date.parse(report.refreshedAt);
  if (!Number.isNaN(parsed)) {
    return parsed;
  }
  return Number.MAX_SAFE_INTEGER - (orderMap.get(report.id) ?? Number.MAX_SAFE_INTEGER);
}

function coverageLabel(value: string | undefined) {
  if (/high/i.test(value ?? "")) return "Deep trace";
  if (/moderate/i.test(value ?? "")) return "Partial trace";
  return "Limited trace";
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
        (a, b) => reportTimestamp(b, orderMap) - reportTimestamp(a, orderMap),
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
      const highRiskLaunches = criticalCount + highCount;
      const sharedFunder =
        typeof latest.behaviourAnalysisV2?.modules?.developer_cluster?.evidence?.shared_funder === "string"
          ? latest.behaviourAnalysisV2.modules.developer_cluster.evidence.shared_funder
          : null;
      const meta = walletLabels.get(key)!;
      const riskyLaunchRatio = Math.round((highRiskLaunches / Math.max(launchCount, 1)) * 100);
      const operatorScore = Math.round(
        clamp(
          avgRugProbability * 0.52 +
            riskyLaunchRatio * 0.28 +
            criticalCount * 7 +
            (profile?.status === "flagged" ? 12 : profile?.status === "watch" ? 6 : 0) +
            cautionWeight(avgTradeCautionLabel(cautionLevels)),
          0,
          100,
        ),
      );
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
        coverage: coverageLabel(profile?.confidence),
        fundingSource: sharedFunder,
        highRiskLaunches,
        latestRefreshedAt: latest.refreshedAt,
        operatorScore,
        profileStatus: profile?.status ?? "clean",
        riskyLaunchRatio,
        summary:
          meta.kind === "wallet"
            ? profile?.summary ??
              `This launch wallet has ${launchCount} tracked launch${launchCount === 1 ? "" : "es"} with ${criticalCount + highCount} high-risk outcomes.`
            : profile?.summary ??
              "We see a meaningful connected-wallet pattern, but the exact upstream launch wallet is still hidden behind the current funding graph.",
        flags: Array.from(new Set(flags)).slice(0, 4),
        topMetrics: profile?.metrics?.slice(0, 4) ?? [],
        profileSignals:
          profile?.signals
            ?.slice()
            .sort((left, right) => {
              const toneWeight = { flagged: 0, watch: 1, neutral: 2 } as const;
              return toneWeight[left.tone] - toneWeight[right.tone];
            })
            .slice(0, 4)
            .map((item) => ({
              label: item.label,
              value: item.value,
              tone: item.tone,
            })) ?? [],
        latestLaunches: ordered.slice(0, 4).map((item) => ({
          id: item.id,
          name: item.name ?? item.displayName,
          symbol: item.symbol ?? item.displayName.slice(0, 5).toUpperCase(),
          risk: item.status,
          pageMode: item.pageMode,
          ageMinutes: item.launchRadar.launchAgeMinutes,
          refreshedAt: item.refreshedAt,
          launchPattern: (() => {
            const pattern = deriveLaunchPatternFromReport(item);
            return pattern ? launchPatternLabel(pattern) : null;
          })(),
        })),
        premiumPrompt:
          meta.kind === "wallet"
            ? "Unlock the full launch wallet profile, related launches, linked addresses, and repeat operator history with Premium."
            : "Unlock the hidden wallet behind this launch cluster, reveal linked addresses, and open the full launch history with Premium.",
      };
    })
    .sort((left, right) => {
      if (right.operatorScore !== left.operatorScore) {
        return right.operatorScore - left.operatorScore;
      }
      if (left.kind !== right.kind) {
        return left.kind === "wallet" ? -1 : 1;
      }
      if (right.launches !== left.launches) {
        return right.launches - left.launches;
      }
      return right.avgRugProbability - left.avgRugProbability;
    });
}
