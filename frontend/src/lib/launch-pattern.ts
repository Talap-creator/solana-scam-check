import type { LaunchFeedItem } from "@/lib/api";
import type { CheckReport } from "@/lib/mock-data";

export type LaunchPattern = "organic" | "sniper" | "insider" | "liquidity_trap";

function includesAnySignal(value: string, needles: string[]) {
  return needles.some((needle) => value.includes(needle));
}

function driverBlob(item: LaunchFeedItem) {
  return [item.summary, ...item.rug_risk_drivers, ...item.trade_caution_drivers].join(" ").toLowerCase();
}

export function deriveLaunchPatternFromFeed(item: LaunchFeedItem): LaunchPattern {
  const signals = driverBlob(item);

  if (
    item.launch_quality === "likely_wash" ||
    (includesAnySignal(signals, ["liquidity", "lp", "drain", "remove liquidity"]) &&
      ["high", "avoid"].includes(item.trade_caution_level))
  ) {
    return "liquidity_trap";
  }

  if (
    includesAnySignal(signals, [
      "insider",
      "developer",
      "linked wallet",
      "coordinated exit",
      "seller wallet",
      "cluster",
    ])
  ) {
    return "insider";
  }

  if (
    item.launch_quality === "coordinated" ||
    item.launch_quality === "noisy" ||
    includesAnySignal(signals, ["early buyer", "aggressive", "sniper", "launch cluster"])
  ) {
    return "sniper";
  }

  return "organic";
}

export function deriveLaunchPatternFromReport(report: CheckReport): LaunchPattern | null {
  if (report.entityType !== "token") {
    return null;
  }

  const modules = report.behaviourAnalysisV2?.modules;
  const developer = modules?.developer_cluster;
  const earlyBuyers = modules?.early_buyers;
  const insiderSelling = modules?.insider_selling;
  const liquidity = modules?.liquidity_management;

  if (
    liquidity?.status === "flagged" &&
    (["high", "avoid"].includes(report.tradeCaution?.level ?? "") ||
      ["high", "critical"].includes(report.launchRisk.level))
  ) {
    return "liquidity_trap";
  }

  if (developer?.status === "flagged" || insiderSelling?.status === "flagged") {
    return "insider";
  }

  if (
    earlyBuyers?.status === "flagged" ||
    earlyBuyers?.status === "watch" ||
    report.launchRadar.earlyClusterActivity !== "none" ||
    report.launchRadar.earlyTradePressure === "aggressive"
  ) {
    return "sniper";
  }

  return "organic";
}

export function launchPatternLabel(pattern: LaunchPattern): string {
  return {
    organic: "Organic",
    sniper: "Sniper",
    insider: "Insider",
    liquidity_trap: "Liquidity trap",
  }[pattern];
}

export function launchPatternSummary(pattern: LaunchPattern): string {
  return {
    organic: "Flow looks comparatively organic across launch age, buyer spread, and current liquidity behaviour.",
    sniper: "Early buyer clustering suggests sniper-style participation and fast launch-window competition.",
    insider: "Developer-linked or insider-style wallet coordination is visible in the current launch profile.",
    liquidity_trap: "Liquidity structure looks unstable enough to resemble a trap setup for fresh entrants.",
  }[pattern];
}

export function launchPatternClass(pattern: LaunchPattern): string {
  return {
    organic: "border-sky-400/30 bg-sky-400/12 text-sky-100",
    sniper: "border-amber-400/30 bg-amber-400/12 text-amber-100",
    insider: "border-orange-400/30 bg-orange-400/12 text-orange-100",
    liquidity_trap: "border-rose-500/30 bg-rose-500/12 text-rose-100",
  }[pattern];
}
