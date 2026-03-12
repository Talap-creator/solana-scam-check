"use client";

import Image from "next/image";
import Link from "next/link";
import { type ReactNode, useEffect, useMemo, useState } from "react";
import { AppIcon } from "@/components/app-icon";
import { RecheckButton } from "@/components/recheck-button";
import { WatchlistToggleButton } from "@/components/watchlist-toggle-button";
import { getAccessToken } from "@/lib/auth";
import { getMe } from "@/lib/api";
import { type CheckReport } from "@/lib/mock-data";

type ReportViewProps = { report: CheckReport };

function shortAddress(value: string) {
  return `${value.slice(0, 4)}...${value.slice(-4)}`;
}

function metricValue(report: CheckReport, labels: string[], fallback: string) {
  for (const label of labels) {
    const metric = report.metrics.find((item) => item.label.toLowerCase() === label.toLowerCase());
    if (metric?.value) return metric.value;
  }
  return fallback;
}

function confidenceDescriptor(report: CheckReport) {
  if (report.confidence >= 0.75) return "High confidence";
  if (report.confidence >= 0.45) return "Moderate confidence";
  return "Limited early data";
}

function confidenceHint(report: CheckReport) {
  if (report.pageMode === "early_launch") {
    return "Confidence is reduced for very new launches because holder, liquidity, and behavioural signals are still forming.";
  }
  if (report.pageMode === "early_market") {
    return "Confidence is still moderated because this token remains inside its first trading day and some market structure is still developing.";
  }
  return "Confidence reflects the current signal coverage across holder structure, liquidity, and behavioural modules.";
}

function pageModeLabel(mode: CheckReport["pageMode"]) {
  if (mode === "early_launch") return "Early Launch Mode";
  if (mode === "early_market") return "Early Market Mode";
  return "Mature Token Mode";
}

function launchRiskLabel(level: CheckReport["launchRisk"]["level"]) {
  if (level === "unknown") return "Unknown";
  return level.charAt(0).toUpperCase() + level.slice(1);
}

function statusTone(level: "low" | "medium" | "high" | "critical" | "unknown" | "avoid" | "moderate") {
  switch (level) {
    case "critical":
    case "avoid":
      return { badge: "border-rose-500/30 bg-rose-500/12 text-rose-200", accent: "text-rose-300", border: "border-rose-500/20" };
    case "high":
      return { badge: "border-orange-500/30 bg-orange-500/12 text-orange-200", accent: "text-orange-200", border: "border-orange-500/20" };
    case "medium":
    case "moderate":
      return { badge: "border-amber-400/30 bg-amber-400/12 text-amber-100", accent: "text-amber-100", border: "border-amber-400/20" };
    case "unknown":
      return { badge: "border-slate-500/30 bg-slate-500/12 text-slate-200", accent: "text-slate-200", border: "border-slate-500/20" };
    default:
      return { badge: "border-sky-400/30 bg-sky-400/12 text-sky-100", accent: "text-sky-100", border: "border-sky-400/20" };
  }
}

function rugEstimateTitle(report: CheckReport) {
  return report.pageMode === "early_launch" ? "Early Rug Estimate" : "Rug Probability";
}

function rugEstimateValue(report: CheckReport) {
  if (report.pageMode === "early_launch") {
    if (report.confidence < 0.35 || report.launchRisk.level === "unknown") return "Too early to classify";
    if (report.rugProbability >= 60) return "Preliminary high";
    if (report.rugProbability >= 30) return "Preliminary medium";
    return "Preliminary low";
  }
  if (report.pageMode === "early_market") return "Limited early estimate";
  return report.status.toUpperCase();
}

function rugEstimateNote(report: CheckReport) {
  if (report.pageMode === "early_launch") {
    return "Early rug probability is secondary during the first launch window and should not be treated as a final verdict.";
  }
  if (report.pageMode === "early_market") {
    return "This probability estimate is still stabilizing because the token remains inside its first trading day.";
  }
  return "Rug probability reflects the combined technical, distribution, behavioural, and maturity model output.";
}

function moduleRows(report: CheckReport) {
  if (report.behaviourAnalysisV2) {
    return Object.entries(report.behaviourAnalysisV2.modules).slice(0, 4).map(([key, item]) => ({
      key,
      title: key === "developer_cluster" ? "Developer Clusters" : key === "early_buyers" ? "Early Buyer Retention" : key === "insider_selling" ? "Insider Selling" : "Liquidity Behaviour",
      subtitle: key === "developer_cluster" ? "Connected Wallets Scan" : key === "early_buyers" ? "T+30 Day Hold Analysis" : key === "insider_selling" ? "Distribution Pressure" : "Pool Management",
      score: item.score,
      summary: item.summary,
    }));
  }
  return report.behaviourAnalysis.slice(0, 4).map((item) => ({
    key: item.key,
    title: item.title,
    subtitle: item.status,
    score: item.tone === "red" ? 82 : item.tone === "orange" ? 64 : item.tone === "yellow" ? 48 : 24,
    summary: item.summary,
  }));
}

function socialShares(report: CheckReport) {
  const bullish = Math.max(15, Math.min(80, Math.round(report.marketMaturity)));
  const bearish = Math.max(10, Math.min(45, Math.round(report.behaviourRisk / 2.2)));
  const neutral = Math.max(10, 100 - bullish - bearish);
  return { bullish, neutral, bearish };
}

function riskDimensionDescription(title: string) {
  switch (title) {
    case "Technical":
      return "Contract permissions and token-level admin controls.";
    case "Distribution":
      return "Holder concentration and early supply spread.";
    case "Market Execution":
      return "Liquidity depth, slippage risk, and exit quality.";
    case "Behavioral":
      return "Coordinated activity, wallet clustering, and insider patterns.";
    default:
      return "Age, listing depth, and maturity stability for this market.";
  }
}

function ReportPaywall({ compact = false }: { compact?: boolean }) {
  return (
    <div className="absolute inset-0 grid place-items-center rounded-[28px] bg-[rgba(2,6,23,0.52)] p-4 backdrop-blur-[9px]">
      <div className={`w-full rounded-[28px] border border-[rgba(59,130,246,0.24)] bg-[linear-gradient(180deg,rgba(8,24,39,0.98),rgba(6,16,30,0.96))] text-center shadow-[0_24px_60px_rgba(2,6,23,0.55)] ${compact ? "max-w-sm p-5" : "max-w-md p-6"}`}>
        <p className="text-[10px] font-bold uppercase tracking-[0.32em] text-[#93c5fd]/75">Premium Access</p>
        <h3 className={`mt-3 font-bold tracking-[-0.05em] text-white ${compact ? "text-2xl" : "text-3xl"}`}>Unlock full report</h3>
        <p className={`mt-3 text-slate-400 ${compact ? "text-xs" : "text-sm"}`}>Register to reveal complete risk modules, execution metrics, and the full behavioral report.</p>
        <div className="mt-5 grid gap-3">
          <Link className="rounded-full bg-[#3b82f6] px-5 py-3 text-center text-sm font-bold text-white" href="/register">Unlock full report</Link>
          <Link className="rounded-full border border-[rgba(59,130,246,0.18)] bg-white/6 px-5 py-3 text-center text-sm font-bold text-slate-100" href="/login">Login</Link>
        </div>
      </div>
    </div>
  );
}

function LockablePanel({ children, locked, compact = false }: { children: ReactNode; locked: boolean; compact?: boolean }) {
  if (!locked) return <>{children}</>;
  return (
    <div className="relative">
      <div className="pointer-events-none select-none blur-[10px] opacity-45 saturate-50">{children}</div>
      <ReportPaywall compact={compact} />
    </div>
  );
}

export function ReportView({ report }: ReportViewProps) {
  const [isAuthed, setIsAuthed] = useState(() => Boolean(getAccessToken()));
  const [shareLabel, setShareLabel] = useState("Share Report");
  const [copyLabel, setCopyLabel] = useState("Copy");
  const modules = useMemo(() => moduleRows(report), [report]);
  const signalsUp = report.riskIncreasers.slice(0, 4);
  const signalsDown = report.riskReducers.slice(0, 4);
  const timeline = report.timeline.slice(0, 6);
  const socials = socialShares(report);
  const marketCap = metricValue(report, ["Market Cap", "Market cap"], "Unavailable");
  const volume = metricValue(report, ["24H Volume", "24h Volume", "Volume 24H"], "Unavailable");
  const price = metricValue(report, ["Price", "Price USD"], "Unavailable");
  const marketAge = metricValue(report, ["Market age"], "Unknown");
  const marketSource = report.marketSource ?? metricValue(report, ["Market source", "Liquidity source"], "Source unavailable");
  const name = report.name ?? report.displayName;
  const symbol = report.symbol ?? report.displayName.slice(0, 5).toUpperCase();
  const launchTone = statusTone(report.launchRisk.level);
  const cautionTone = statusTone(report.tradeCaution?.level ?? "moderate");
  const rugTone = statusTone(report.status);
  const confidenceTone = report.confidence >= 0.75 ? statusTone("low") : report.confidence >= 0.45 ? statusTone("moderate") : statusTone("unknown");
  const isEarly = report.pageMode !== "mature";

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        await getMe();
        if (!cancelled) {
          setIsAuthed(true);
        }
      } catch {
        if (!cancelled) {
          setIsAuthed(false);
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const copyShareLink = async () => {
    if (typeof window === "undefined") return;
    try {
      await navigator.clipboard.writeText(window.location.href);
      setShareLabel("Link Copied");
      window.setTimeout(() => setShareLabel("Share Report"), 1800);
    } catch {
      setShareLabel("Copy Failed");
      window.setTimeout(() => setShareLabel("Share Report"), 1800);
    }
  };

  const copyMintAddress = async () => {
    if (typeof window === "undefined") return;
    try {
      await navigator.clipboard.writeText(report.entityId);
      setCopyLabel("Copied");
      window.setTimeout(() => setCopyLabel("Copy"), 1800);
    } catch {
      setCopyLabel("Failed");
      window.setTimeout(() => setCopyLabel("Copy"), 1800);
    }
  };

  const dimensions = [
    { title: "Technical", score: report.technicalRisk, icon: "code" as const },
    { title: "Distribution", score: report.distributionRisk, icon: "groups" as const },
    { title: "Market Execution", score: report.marketExecutionRisk, icon: "chart" as const },
    { title: "Behavioral", score: report.behaviourRisk, icon: "hub" as const },
    { title: "Market Maturity", score: report.marketMaturity, icon: "hourglass" as const },
  ];

  return (
    <main className="min-h-screen bg-[#050b1a] text-slate-100">
      <div className="relative flex min-h-screen flex-col overflow-x-hidden bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.12),transparent_24%),linear-gradient(180deg,#050b1a_0%,#071228_100%)]">
        <header className="sticky top-0 z-50 border-b border-white/10 bg-[rgba(3,9,21,0.82)] px-4 py-3 backdrop-blur-md lg:px-10">
          <div className="mx-auto flex max-w-[1440px] items-center justify-between">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-3 text-primary">
                <AppIcon className="h-8 w-8" name="shield" />
                <h2 className="text-xl font-bold tracking-tight text-white">SolanaTrust</h2>
              </div>
              <nav className="hidden items-center gap-6 md:flex">
                <Link className="text-sm font-medium text-slate-400 transition-colors hover:text-primary" href="/dashboard">Dashboard</Link>
                <span className="border-b-2 border-primary pb-1 text-sm font-medium text-white">Token Analyzer</span>
                <Link className="text-sm font-medium text-slate-400 transition-colors hover:text-primary" href="/coins">Launch Feed</Link>
              </nav>
            </div>
            <div className="flex items-center gap-3">
              <RecheckButton entityId={report.entityId} entityType={report.entityType} />
              <Link className="rounded-full border border-white/12 bg-white/6 px-5 py-2 text-sm font-bold text-white" href="/login">Log In</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1440px] flex-1 px-4 py-6 md:px-10">
          <section className="rounded-[32px] border border-white/10 bg-[linear-gradient(180deg,rgba(18,30,53,0.96),rgba(8,16,30,0.96))] p-6 shadow-[0_24px_90px_rgba(2,6,23,0.4)] lg:p-8">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
              <div className="flex items-start gap-5">
                <div className="relative h-20 w-20 overflow-hidden rounded-[22px] border border-primary/25 bg-primary/10">
                  {report.logoUrl ? <Image alt={name} className="h-full w-full object-cover" fill sizes="80px" src={report.logoUrl} /> : <div className="grid h-full w-full place-items-center text-3xl font-black text-primary">{symbol.slice(0, 1)}</div>}
                </div>
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.24em] text-primary/80">{pageModeLabel(report.pageMode)}</span>
                    <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium text-slate-300">{marketAge}</span>
                    <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium text-slate-300">{marketSource}</span>
                  </div>
                  <div>
                    <div className="flex flex-wrap items-end gap-3">
                      <h1 className="text-3xl font-bold tracking-[-0.05em] text-white lg:text-4xl">{name}</h1>
                      <span className="pb-1 text-lg font-mono text-slate-400">{symbol}</span>
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-slate-400">
                      <span className="font-mono">{shortAddress(report.entityId)}</span>
                      <button className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-200 transition hover:border-primary/30 hover:text-primary" onClick={() => void copyMintAddress()} type="button">
                        <AppIcon className="h-4 w-4" name="copy" />
                        {copyLabel}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <WatchlistToggleButton displayName={name} entityId={report.entityId} entityType={report.entityType} />
                <button className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/6 px-5 py-3 text-sm font-bold text-slate-100 transition hover:border-primary/20 hover:text-primary" onClick={() => void copyShareLink()} type="button">
                  <AppIcon className="h-5 w-5" name="share" />
                  {shareLabel}
                </button>
              </div>
            </div>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <article className={`rounded-[26px] border bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-5 ${launchTone.border}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-slate-400">Launch Risk</p>
                    <h3 className={`mt-3 text-3xl font-black tracking-[-0.05em] ${launchTone.accent}`}>{launchRiskLabel(report.launchRisk.level)}</h3>
                  </div>
                  <div className={`rounded-2xl border p-3 ${launchTone.badge}`}><AppIcon className="h-6 w-6" name="rocket" /></div>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{report.launchRisk.summary}</p>
                <div className="mt-4 space-y-2">
                  {report.launchRisk.drivers.slice(0, 2).map((item) => <div key={item} className="rounded-2xl border border-white/8 bg-white/4 px-3 py-2 text-xs text-slate-300">{item}</div>)}
                </div>
              </article>

              <article className={`rounded-[26px] border bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-5 ${cautionTone.border}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-slate-400">Trade Caution</p>
                    <h3 className={`mt-3 text-3xl font-black tracking-[-0.05em] ${cautionTone.accent}`}>{report.tradeCaution?.label ?? "Moderate caution"}</h3>
                  </div>
                  <div className={`rounded-2xl border p-3 ${cautionTone.badge}`}><AppIcon className="h-6 w-6" name="chart" /></div>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{report.tradeCaution?.summary ?? "Trade setup is still stabilizing while live execution conditions develop."}</p>
                <p className="mt-4 text-xs font-mono uppercase tracking-[0.2em] text-slate-500">Score {report.tradeCaution?.score ?? report.marketExecutionRisk}</p>
              </article>

              <article className={`rounded-[26px] border bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-5 ${rugTone.border}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-slate-400">{rugEstimateTitle(report)}</p>
                    <h3 className={`mt-3 text-3xl font-black tracking-[-0.05em] ${rugTone.accent}`}>{rugEstimateValue(report)}</h3>
                  </div>
                  <div className={`rounded-2xl border p-3 ${rugTone.badge}`}><AppIcon className="h-6 w-6" name="verified-user" /></div>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{rugEstimateNote(report)}</p>
                <p className="mt-4 text-xs font-mono uppercase tracking-[0.2em] text-slate-500">{report.rugProbability}% model output</p>
              </article>

              <article className={`rounded-[26px] border bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-5 ${confidenceTone.border}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-slate-400">Confidence</p>
                    <h3 className={`mt-3 text-3xl font-black tracking-[-0.05em] ${confidenceTone.accent}`}>{confidenceDescriptor(report)}</h3>
                  </div>
                  <div className={`rounded-2xl border p-3 ${confidenceTone.badge}`}><AppIcon className="h-6 w-6" name="hourglass" /></div>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{confidenceHint(report)}</p>
                <p className="mt-4 text-xs font-mono uppercase tracking-[0.2em] text-slate-500">{report.confidence.toFixed(2)} confidence score</p>
              </article>
            </div>
          </section>

          <section className="mt-6 rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(26,39,63,0.95),rgba(13,22,39,0.96))]">
            <div className="flex items-center gap-3 border-b border-white/10 px-6 py-4">
              <AppIcon className="h-5 w-5 text-primary" name="document" />
              <h3 className="text-lg font-bold text-white">Security Summary</h3>
            </div>
            <div className="grid gap-6 p-6 lg:grid-cols-[minmax(0,1fr)_280px]">
              <div>
                <p className="text-lg leading-8 text-slate-200">{report.summary}</p>
                <div className="mt-5 flex flex-wrap gap-2">
                  {(signalsDown.length ? signalsDown : report.launchRisk.drivers.map((item, index) => ({ code: `launch-driver-${index}`, label: item, explanation: item, severity: "low" as const, weight: 0 }))).slice(0, 3).map((item) => <span key={item.code} className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs text-primary">{item.label}</span>)}
                </div>
              </div>
              <div className="rounded-[24px] border border-white/10 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.3),transparent_56%),linear-gradient(180deg,rgba(5,12,24,0.92),rgba(6,13,26,0.98))] p-5">
                <p className="text-[11px] font-bold uppercase tracking-[0.26em] text-slate-500">Current posture</p>
                <p className="mt-4 text-2xl font-black tracking-[-0.05em] text-white">{pageModeLabel(report.pageMode)}</p>
                <p className="mt-3 text-sm leading-6 text-slate-300">{report.launchRadar.summary}</p>
              </div>
            </div>
          </section>

          {isEarly ? <section className="mt-6 rounded-[28px] border border-primary/15 bg-[linear-gradient(180deg,rgba(6,18,34,0.96),rgba(5,12,24,0.98))] p-6"><div className="flex items-center gap-3"><div className="rounded-2xl border border-primary/20 bg-primary/10 p-3 text-primary"><AppIcon className="h-5 w-5" name="info" /></div><div><h3 className="text-lg font-bold text-white">Why this verdict is still early</h3><p className="mt-1 text-sm text-slate-400">Token age is still low, holder structure can still change, behavioural signals may not have emerged yet, and liquidity conditions can shift rapidly during launch.</p></div></div></section> : null}

          <section className="mt-6 rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-6">
            <div className="flex items-center gap-3"><div className="rounded-2xl border border-primary/20 bg-primary/10 p-3 text-primary"><AppIcon className="h-5 w-5" name="radar" /></div><div><h3 className="text-lg font-bold text-white">Launch Radar</h3><p className="mt-1 text-sm text-slate-400">Early launch-specific signals, separate from mature behavioural and scam-history scoring.</p></div></div>
            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {[
                { label: "Launch age", value: report.launchRadar.launchAgeMinutes !== null ? `${report.launchRadar.launchAgeMinutes}m` : marketAge },
                { label: "Initial liquidity band", value: report.launchRadar.initialLiquidityBand },
                { label: "Early trade pressure", value: report.launchRadar.earlyTradePressure },
                { label: "Launch concentration", value: report.launchRadar.launchConcentration },
                { label: "Copycat / name collision", value: report.launchRadar.copycatStatus },
                { label: "Early cluster activity", value: report.launchRadar.earlyClusterActivity },
              ].map((item) => <article key={item.label} className="rounded-[22px] border border-white/8 bg-white/[0.03] p-4"><p className="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">{item.label}</p><p className="mt-3 text-lg font-semibold capitalize text-white">{item.value}</p></article>)}
            </div>
            <p className="mt-5 max-w-4xl text-sm leading-7 text-slate-300">{report.launchRadar.summary}</p>
          </section>

          <section className="mt-6 rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-6">
            <div className="flex items-center gap-3"><div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-200"><AppIcon className="h-5 w-5" name="warning" /></div><div><h3 className="text-lg font-bold text-white">Early Warnings</h3><p className="mt-1 text-sm text-slate-400">Compact launch alerts that explain what still looks unstable right now.</p></div></div>
            <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {(report.earlyWarnings.length ? report.earlyWarnings : ["No acute early-launch warnings are active right now."]).map((item) => <div key={item} className="rounded-[22px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-200">{item}</div>)}
            </div>
          </section>

          <section className="mt-6 rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-6">
            <div className="flex items-center gap-3"><div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-200"><AppIcon className="h-5 w-5" name="analytics" /></div><div><h3 className="text-lg font-bold text-white">Risk Dimensions</h3><p className="mt-1 text-sm text-slate-400">Five dimensions that feed the final token assessment.</p></div></div>
            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
              {dimensions.map((item) => {
                const tone = statusTone(item.score >= 75 ? "critical" : item.score >= 50 ? "high" : item.score >= 25 ? "medium" : "low");
                const isMaturityContext = report.pageMode === "early_launch" && item.title === "Market Maturity";
                return <article key={item.title} className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"><div className="flex items-center justify-between"><div className={`rounded-2xl border p-3 ${tone.badge}`}><AppIcon className="h-5 w-5" name={item.icon} /></div>{isMaturityContext ? <span className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.24em] text-primary">Context only</span> : <span className="rounded-full border border-white/10 bg-white/6 px-3 py-1 text-xs font-mono text-slate-200">{item.score}/100</span>}</div><h4 className="mt-4 text-lg font-bold text-white">{item.title}</h4><p className="mt-2 text-sm leading-6 text-slate-400">{isMaturityContext ? "Too early to establish a reliable maturity profile." : riskDimensionDescription(item.title)}</p>{isMaturityContext ? null : <div className="mt-4 h-2 overflow-hidden rounded-full bg-[#0b1325]"><div className="h-full rounded-full bg-[linear-gradient(90deg,#3b82f6,#60a5fa)]" style={{ width: `${Math.max(12, item.score)}%` }} /></div>}</article>;
              })}
            </div>
          </section>

          <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
            <LockablePanel locked={!isAuthed}>
              <div className="space-y-6">
                <section className="rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-6">
                  <div className="flex items-center gap-3"><div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-200"><AppIcon className="h-5 w-5" name="hub" /></div><div><h3 className="text-lg font-bold text-white">Behavioral Analysis</h3><p className="mt-1 text-sm text-slate-400">Wallet coordination, exit patterns, and live liquidity behaviour.</p></div></div>
                  {report.pageMode === "early_launch" ? <div className="mt-5 rounded-[22px] border border-primary/15 bg-primary/8 px-4 py-3 text-sm leading-6 text-slate-300">Behaviour modules are less reliable during the first minutes of trading because coordinated patterns and insider exits may not have emerged yet.</div> : null}
                  <div className="mt-6 grid gap-4 md:grid-cols-2">
                    {modules.map((item) => {
                      const tone = statusTone(item.score >= 75 ? "critical" : item.score >= 55 ? "high" : item.score >= 30 ? "medium" : "low");
                      return <article key={item.key} className="rounded-[24px] border border-white/8 bg-white/[0.03] p-5"><div className="flex items-center gap-3"><div className={`rounded-2xl border p-3 ${tone.badge}`}><AppIcon className="h-5 w-5" name={item.key.includes("developer") ? "hub" : item.key.includes("early") ? "history" : item.key.includes("insider") ? "chart" : "drop"} /></div><div><h4 className="text-sm font-bold text-white">{item.title}</h4><p className="text-[10px] uppercase tracking-[0.22em] text-slate-500">{item.subtitle}</p></div></div><div className="mt-5"><div className="mb-2 flex items-center justify-between text-xs"><span className="text-slate-500">Module score</span><span className="font-mono text-slate-200">{item.score}</span></div><div className="h-2 overflow-hidden rounded-full bg-[#0b1325]"><div className="h-full rounded-full bg-[linear-gradient(90deg,#3b82f6,#60a5fa)]" style={{ width: `${Math.max(14, Math.min(item.score, 100))}%` }} /></div></div><p className="mt-4 text-sm leading-6 text-slate-300">{item.summary}</p></article>;
                    })}
                  </div>
                </section>

                <section className="rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-6">
                  <div className="flex items-center gap-3"><div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-200"><AppIcon className="h-5 w-5" name="sensors" /></div><div><h3 className="text-lg font-bold text-white">Top Signals</h3><p className="mt-1 text-sm text-slate-400">The strongest risk reducers and increasers visible in the current report.</p></div></div>
                  <div className="mt-6 grid gap-6 lg:grid-cols-2">
                    <div>
                      <h4 className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.26em] text-primary"><AppIcon className="h-4 w-4" name="arrow-down" />Reducing Risk</h4>
                      <div className="space-y-3">{(signalsDown.length ? signalsDown : [{ code: "no-reducers", explanation: "No material reducing signals were detected yet." }]).map((item) => <div key={item.code} className="rounded-[22px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm leading-6 text-slate-200">{item.explanation}</div>)}</div>
                    </div>
                    <div>
                      <h4 className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.26em] text-rose-300"><AppIcon className="h-4 w-4" name="arrow-up" />Increasing Risk</h4>
                      <div className="space-y-3">{signalsUp.map((item) => <div key={item.code} className="rounded-[22px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm leading-6 text-slate-200">{item.explanation}</div>)}</div>
                    </div>
                  </div>
                </section>
              </div>
            </LockablePanel>

            <LockablePanel compact locked={!isAuthed}>
              <div className="space-y-6">
                <section className="rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-6">
                  <div className="flex items-center gap-3"><div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-200"><AppIcon className="h-5 w-5" name="chart" /></div><div><h3 className="text-lg font-bold text-white">Market Execution</h3><p className="mt-1 text-sm text-slate-400">Trader-facing entry and exit conditions in the detected pool.</p></div></div>
                  <div className="mt-6 space-y-4">
                    <div className="flex items-end justify-between"><div><p className="mb-1 text-xs text-slate-500">Price USD</p><p className="font-mono text-2xl font-bold text-white">{price}</p></div><div className="text-right"><p className={`text-sm font-bold ${cautionTone.accent}`}>{report.tradeCaution?.label ?? "Moderate caution"}</p><p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Current setup</p></div></div>
                    <div className="space-y-3 border-t border-white/10 pt-4">
                      <div className="flex justify-between text-sm"><span className="text-slate-500">Market Cap</span><span className="text-slate-200">{marketCap}</span></div>
                      <div className="flex justify-between text-sm"><span className="text-slate-500">24H Volume</span><span className="text-slate-200">{volume}</span></div>
                      <div className="flex justify-between text-sm"><span className="text-slate-500">Liquidity</span><span className="text-slate-200">{report.liquidity}</span></div>
                    </div>
                  </div>
                </section>

                <section className="rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-6">
                  <div className="flex items-center gap-3"><div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-200"><AppIcon className="h-5 w-5" name="happy-face" /></div><div><h3 className="text-lg font-bold text-white">Social Sentiment</h3><p className="mt-1 text-sm text-slate-400">Lightweight market mood split based on maturity and behaviour pressure.</p></div></div>
                  <div className="mt-6 flex items-center justify-between gap-2">
                    <div className="flex flex-1 flex-col items-center"><AppIcon className="mb-1 h-5 w-5 text-primary" name="happy-face" /><span className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Bullish</span><span className="text-lg font-bold text-white">{socials.bullish}%</span></div>
                    <div className="h-8 w-px bg-white/10" />
                    <div className="flex flex-1 flex-col items-center"><AppIcon className="mb-1 h-5 w-5 text-slate-500" name="neutral-face" /><span className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Neutral</span><span className="text-lg font-bold text-white">{socials.neutral}%</span></div>
                    <div className="h-8 w-px bg-white/10" />
                    <div className="flex flex-1 flex-col items-center"><AppIcon className="mb-1 h-5 w-5 text-rose-300" name="sad-face" /><span className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Bearish</span><span className="text-lg font-bold text-white">{socials.bearish}%</span></div>
                  </div>
                </section>
              </div>
            </LockablePanel>
          </div>

          <section className="mt-6 rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-6">
            <div className="flex items-center gap-3"><div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-200"><AppIcon className="h-5 w-5" name="history" /></div><div><h3 className="text-lg font-bold text-white">Timeline</h3><p className="mt-1 text-sm text-slate-400">Fresh launches emphasize event sequence because timing matters as much as static scores.</p></div></div>
            <div className="relative mt-6 pl-4">
              <div className="absolute bottom-2 left-2 top-2 w-px bg-white/10" />
              <div className="space-y-6">
                {timeline.map((item, index) => {
                  const tone = item.tone === "danger" ? "bg-rose-400 ring-rose-400/20" : item.tone === "warn" ? "bg-amber-300 ring-amber-300/20" : "bg-primary ring-primary/20";
                  return <div key={`${item.label}-${index}`} className="relative pl-8"><div className={`absolute left-0 top-1.5 h-4 w-4 rounded-full ring-4 ${tone}`} /><p className="text-[11px] font-mono uppercase tracking-[0.18em] text-slate-500">{report.refreshedAt}</p><h4 className="mt-1 text-sm font-bold text-white">{item.label}</h4><p className="mt-1 text-sm leading-6 text-slate-300">{item.value}</p></div>;
                })}
              </div>
            </div>
          </section>

          <section className="mt-6 rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(7,16,31,0.94),rgba(5,11,22,0.98))] p-6">
            <div className="flex items-start gap-3"><div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-200"><AppIcon className="h-5 w-5" name="info" /></div><div><h3 className="text-lg font-bold text-white">Disclaimer</h3><p className="mt-2 max-w-5xl text-sm leading-7 text-slate-400">{report.pageMode === "early_launch" ? "Very new launches can change quickly. Low current signal visibility does not mean low final risk, and additional holder or liquidity behaviour may appear as trading continues." : report.pageMode === "early_market" ? "First-day assessments are more stable than minute-one launch reads, but holder concentration, liquidity conditions, and behavioural anomalies can still change materially." : "This report is a probabilistic risk assessment, not a guarantee. Traders should still verify token contracts, liquidity ownership, and execution conditions before entering a position."}</p></div></div>
          </section>
        </main>

        <footer className="mt-12 border-t border-white/10 bg-[rgba(3,9,21,0.65)] px-4 py-8 md:px-10">
          <div className="mx-auto flex max-w-[1440px] flex-col items-center justify-between gap-6 md:flex-row">
            <div className="flex items-center gap-2 opacity-60">
              <AppIcon className="h-5 w-5" name="shield" />
              <span className="text-sm font-bold text-slate-300">SolanaTrust v2.4.1</span>
            </div>
            <div className="flex gap-8">
              <Link className="text-xs text-slate-500 transition-colors hover:text-primary" href="/login">Terms of Service</Link>
              <Link className="text-xs text-slate-500 transition-colors hover:text-primary" href="/login">Privacy Policy</Link>
              <Link className="text-xs text-slate-500 transition-colors hover:text-primary" href="/coins">API Documentation</Link>
            </div>
            <p className="text-xs text-slate-500">(c) 2024 SolanaTrust Analysis Labs.</p>
          </div>
        </footer>
      </div>
    </main>
  );
}
