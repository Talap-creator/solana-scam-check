"use client";

import { useMemo, useState } from "react";
import { AppIcon } from "@/components/app-icon";
import { PremiumCheckoutButton } from "@/components/premium-checkout-button";
import type { DeveloperLeadProfile } from "@/lib/developer-leads";

type DeveloperWalletBoardProps = {
  profiles: DeveloperLeadProfile[];
};

type BoardTab = "all" | "wallets" | "clusters" | "high-risk" | "active";
type BoardSort = "operator" | "launches" | "risky" | "recent" | "confidence";

const TAB_OPTIONS: Array<{ key: BoardTab; label: string }> = [
  { key: "all", label: "All operators" },
  { key: "wallets", label: "Resolved wallets" },
  { key: "clusters", label: "Hidden clusters" },
  { key: "high-risk", label: "High risk" },
  { key: "active", label: "Active now" },
];

const SORT_OPTIONS: Array<{ key: BoardSort; label: string }> = [
  { key: "operator", label: "Highest operator score" },
  { key: "launches", label: "Most launches" },
  { key: "risky", label: "Most risky launches" },
  { key: "recent", label: "Latest activity" },
  { key: "confidence", label: "Strongest confidence" },
];

function modeLabel(value: DeveloperLeadProfile["latestLaunches"][number]["pageMode"]) {
  if (value === "early_launch") return "Early launch";
  if (value === "early_market") return "Early market";
  return "Mature";
}

function walletKindLabel(profile: DeveloperLeadProfile) {
  return profile.kind === "wallet" ? "Launch wallet" : "Wallet cluster";
}

function cautionTone(value: string) {
  if (/avoid/i.test(value)) return "text-rose-300";
  if (/high/i.test(value)) return "text-orange-200";
  if (/moderate/i.test(value)) return "text-amber-200";
  return "text-emerald-200";
}

function confidenceWeight(value: string) {
  if (/high/i.test(value)) return 3;
  if (/moderate/i.test(value)) return 2;
  return 1;
}

function statusClasses(status: DeveloperLeadProfile["profileStatus"]) {
  if (status === "flagged") return "border-rose-500/20 bg-rose-500/10 text-rose-200";
  if (status === "watch") return "border-amber-400/20 bg-amber-400/10 text-amber-100";
  return "border-emerald-400/20 bg-emerald-400/10 text-emerald-100";
}

function signalTone(tone: "neutral" | "watch" | "flagged") {
  if (tone === "flagged") return "border-rose-500/20 bg-rose-500/10 text-rose-200";
  if (tone === "watch") return "border-amber-400/20 bg-amber-400/10 text-amber-100";
  return "border-white/10 bg-white/[0.03] text-slate-200";
}

function operatorClasses(score: number) {
  if (score >= 75) return "border-rose-500/20 bg-rose-500/10 text-rose-200";
  if (score >= 55) return "border-orange-400/20 bg-orange-400/10 text-orange-100";
  if (score >= 35) return "border-amber-400/20 bg-amber-400/10 text-amber-100";
  return "border-sky-400/20 bg-sky-400/10 text-sky-100";
}

function operatorBar(score: number) {
  if (score >= 75) return "bg-rose-400";
  if (score >= 55) return "bg-orange-400";
  if (score >= 35) return "bg-amber-400";
  return "bg-[#60a5fa]";
}

function relativeTimeLabel(value: string) {
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) return "Unknown";
  const diffMinutes = Math.max(0, Math.round((Date.now() - parsed) / 60000));
  if (diffMinutes < 1) return "Just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.round(diffHours / 24)}d ago`;
}

function launchAgeLabel(value: number | null) {
  if (typeof value !== "number") return "Age n/a";
  if (value < 60) return `${Math.round(value)}m old`;
  if (value < 1440) return `${(value / 60).toFixed(1)}h old`;
  return `${(value / 1440).toFixed(1)}d old`;
}

function latestActivityValue(profile: DeveloperLeadProfile) {
  const parsed = Date.parse(profile.latestRefreshedAt);
  if (!Number.isNaN(parsed)) return parsed;
  const ageMinutes = profile.latestLaunches[0]?.ageMinutes;
  if (typeof ageMinutes === "number") return Date.now() - ageMinutes * 60000;
  return 0;
}

function profileMatchesQuery(profile: DeveloperLeadProfile, query: string) {
  if (!query) return true;
  const haystack = [
    profile.label,
    profile.walletPreview,
    profile.summary,
    profile.fundingSource ?? "",
    ...profile.flags,
    ...profile.latestLaunches.flatMap((item) => [item.name, item.symbol, item.launchPattern ?? "", item.risk]),
    ...profile.profileSignals.flatMap((item) => [item.label, item.value]),
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query.toLowerCase());
}

export function DeveloperWalletBoard({ profiles }: DeveloperWalletBoardProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState<BoardTab>("all");
  const [sort, setSort] = useState<BoardSort>("operator");

  const filteredProfiles = useMemo(() => {
    let items = profiles.filter((profile) => profileMatchesQuery(profile, query));

    items = items.filter((profile) => {
      if (tab === "wallets") return profile.kind === "wallet";
      if (tab === "clusters") return profile.kind === "cluster" || profile.unresolved;
      if (tab === "high-risk") return profile.operatorScore >= 60 || profile.highRiskLaunches > 0;
      if (tab === "active") return (profile.latestLaunches[0]?.ageMinutes ?? Number.MAX_SAFE_INTEGER) <= 1440;
      return true;
    });

    return [...items].sort((left, right) => {
      if (sort === "launches") {
        if (right.launches !== left.launches) return right.launches - left.launches;
        return right.operatorScore - left.operatorScore;
      }
      if (sort === "risky") {
        if (right.highRiskLaunches !== left.highRiskLaunches) return right.highRiskLaunches - left.highRiskLaunches;
        return right.avgRugProbability - left.avgRugProbability;
      }
      if (sort === "recent") return latestActivityValue(right) - latestActivityValue(left);
      if (sort === "confidence") {
        const diff = confidenceWeight(right.confidence) - confidenceWeight(left.confidence);
        if (diff !== 0) return diff;
      }
      return right.operatorScore - left.operatorScore;
    });
  }, [profiles, query, sort, tab]);

  const selected = useMemo(
    () => filteredProfiles.find((item) => item.id === selectedId) ?? profiles.find((item) => item.id === selectedId) ?? null,
    [filteredProfiles, profiles, selectedId],
  );

  const walletCount = profiles.filter((item) => item.kind === "wallet").length;
  const clusterCount = profiles.filter((item) => item.kind === "cluster").length;
  const repeatOperators = profiles.filter((item) => item.launches >= 2).length;
  const avgOperatorScore = profiles.length
    ? Math.round(profiles.reduce((total, item) => total + item.operatorScore, 0) / profiles.length)
    : 0;

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-[24px] border border-white/10 bg-[#020617] px-5 py-5">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Resolved wallets</p>
          <p className="mt-3 text-3xl font-black text-white">{walletCount}</p>
          <p className="mt-2 text-sm text-slate-400">Launch wallets resolved from shared funding routes.</p>
        </article>
        <article className="rounded-[24px] border border-white/10 bg-[#020617] px-5 py-5">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Hidden clusters</p>
          <p className="mt-3 text-3xl font-black text-white">{clusterCount}</p>
          <p className="mt-2 text-sm text-slate-400">Operators still hidden behind the funding graph.</p>
        </article>
        <article className="rounded-[24px] border border-white/10 bg-[#020617] px-5 py-5">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Repeat operators</p>
          <p className="mt-3 text-3xl font-black text-white">{repeatOperators}</p>
          <p className="mt-2 text-sm text-slate-400">Wallets or clusters tied to more than one tracked launch.</p>
        </article>
        <article className="rounded-[24px] border border-white/10 bg-[#020617] px-5 py-5">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Average operator score</p>
          <p className="mt-3 text-3xl font-black text-white">{avgOperatorScore}</p>
          <p className="mt-2 text-sm text-slate-400">Weighted from rug risk, caution, and linked-wallet evidence.</p>
        </article>
      </div>

      {profiles.length ? (
        <div className="mt-6 overflow-hidden rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))]">
          <div className="border-b border-white/10 px-5 py-5">
            <div className="grid gap-5 xl:grid-cols-[minmax(0,1.4fr)_380px]">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded bg-[#3b82f6]/10 px-2 py-0.5 text-[11px] font-mono font-bold uppercase tracking-[0.22em] text-[#93c5fd]">
                    Wallet Intel
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">launch-wallet-board.v1</span>
                </div>
                <h2 className="mt-3 text-3xl font-black uppercase italic tracking-tight text-white md:text-[2.6rem]">
                  Developer Wallet Feed
                </h2>
                <p className="mt-2 max-w-3xl text-sm text-slate-400">
                  Ranked wallets and launch clusters surfaced from recent token reports: shared funders, repeat launches,
                  linked exits, hidden clusters, and operator reputation in one board.
                </p>
              </div>

              <div className="rounded-2xl border border-[#3b82f6]/20 bg-[#3b82f6]/5 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Board status</p>
                    <p className="mt-2 text-lg font-bold text-white">
                      {filteredProfiles.length} operator{filteredProfiles.length === 1 ? "" : "s"} visible
                    </p>
                    <p className="mt-1 text-sm text-slate-400">
                      Premium opens the full wallet history, linked launch graph, and hidden-cluster resolution.
                    </p>
                  </div>
                  <span className="inline-flex items-center gap-2 rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.12em] text-[#93c5fd]">
                    <span className="h-2 w-2 rounded-full bg-[#3b82f6]" />
                    LIVE SIGNALS
                  </span>
                </div>

                <label className="mt-4 flex items-center gap-2 rounded-xl border border-[#3b82f6]/20 bg-[#020617] px-3 py-3">
                  <AppIcon className="h-5 w-5 text-[#60a5fa]" name="search" />
                  <input
                    className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-500"
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search wallet, cluster, launch, or signal"
                    value={query}
                  />
                </label>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3">
                    <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Visible wallets</p>
                    <p className="mt-1 text-sm font-semibold text-white">{filteredProfiles.filter((item) => item.kind === "wallet").length}</p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3">
                    <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Avg operator score</p>
                    <p className="mt-1 text-sm font-semibold text-white">
                      {filteredProfiles.length
                        ? Math.round(filteredProfiles.reduce((total, item) => total + item.operatorScore, 0) / filteredProfiles.length)
                        : 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-3">
              {TAB_OPTIONS.map((item) => {
                const active = tab === item.key;
                return (
                  <button
                    key={item.key}
                    className={
                      active
                        ? "rounded-lg bg-[#3b82f6] px-4 py-2 text-sm font-bold uppercase tracking-tight text-white shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                        : "rounded-lg border border-[#3b82f6]/30 bg-[#3b82f6]/10 px-4 py-2 text-sm font-bold uppercase tracking-tight text-[#93c5fd] transition hover:bg-[#3b82f6]/20"
                    }
                    onClick={() => setTab(item.key)}
                    type="button"
                  >
                    {item.label}
                  </button>
                );
              })}
              <div className="ml-auto flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
                <select
                  className="rounded-lg border border-[#3b82f6]/20 bg-[#020617] px-4 py-3 text-sm text-white outline-none"
                  onChange={(event) => setSort(event.target.value as BoardSort)}
                  value={sort}
                >
                  {SORT_OPTIONS.map((option) => (
                    <option key={option.key} value={option.key}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <button
                  className="rounded-lg border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-4 py-3 text-sm font-semibold text-[#93c5fd]"
                  onClick={() => {
                    setQuery("");
                    setTab("all");
                    setSort("operator");
                  }}
                  type="button"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>

          <div className="hidden overflow-x-auto lg:block">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-white/8 bg-white/[0.02] text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">
                <tr>
                  <th className="px-5 py-4">Wallet</th>
                  <th className="px-5 py-4">Operator score</th>
                  <th className="px-5 py-4">Launches</th>
                  <th className="px-5 py-4">Funding trace</th>
                  <th className="px-5 py-4">Latest launch</th>
                  <th className="px-5 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/8">
                {filteredProfiles.map((profile) => {
                  const latest = profile.latestLaunches[0];
                  return (
                    <tr key={profile.id} className="transition hover:bg-white/[0.03]">
                      <td className="px-5 py-4 align-top">
                        <div className="min-w-[280px]">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#93c5fd]">
                              {walletKindLabel(profile)}
                            </span>
                            <span className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${statusClasses(profile.profileStatus)}`}>
                              {profile.profileStatus}
                            </span>
                            {profile.unresolved ? (
                              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-300">
                                Hidden source
                              </span>
                            ) : null}
                          </div>
                          <p className="mt-3 text-base font-bold text-white">{profile.label}</p>
                          <p className="mt-1 text-xs text-slate-500">{profile.walletPreview}</p>
                          <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">{profile.summary}</p>
                          {profile.flags.length ? (
                            <div className="mt-3 flex flex-wrap gap-2">
                              {profile.flags.slice(0, 3).map((flag) => (
                                <span
                                  key={flag}
                                  className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-300"
                                >
                                  {flag}
                                </span>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      </td>
                      <td className="px-5 py-4 align-top">
                        <div className="min-w-[180px]">
                          <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-bold ${operatorClasses(profile.operatorScore)}`}>
                            Score {profile.operatorScore}
                          </span>
                          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/10">
                            <div className={`h-full rounded-full ${operatorBar(profile.operatorScore)}`} style={{ width: `${profile.operatorScore}%` }} />
                          </div>
                          <p className={`mt-3 text-sm font-semibold ${cautionTone(profile.avgTradeCaution)}`}>{profile.avgTradeCaution}</p>
                          <p className="mt-1 text-xs text-slate-500">
                            {profile.highRiskLaunches} risky launch{profile.highRiskLaunches === 1 ? "" : "es"} | {profile.riskyLaunchRatio}% ratio
                          </p>
                        </div>
                      </td>
                      <td className="px-5 py-4 align-top">
                        <div className="min-w-[160px]">
                          <p className="text-lg font-bold text-white">{profile.launches}</p>
                          <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">{profile.confidence}</p>
                          <p className="mt-1 text-xs text-slate-400">{profile.coverage}</p>
                        </div>
                      </td>
                      <td className="px-5 py-4 align-top">
                        <div className="min-w-[220px] space-y-2">
                          <div>
                            <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Funding source</p>
                            <p className="mt-1 text-sm font-semibold text-white">{profile.fundingSource ?? "Hidden / unresolved"}</p>
                          </div>
                          {profile.profileSignals.slice(0, 2).map((signal) => (
                            <div key={signal.label} className={`rounded-2xl border px-3 py-2 text-xs ${signalTone(signal.tone)}`}>
                              <p className="font-bold uppercase tracking-[0.16em]">{signal.label}</p>
                              <p className="mt-1 text-sm font-semibold">{signal.value}</p>
                            </div>
                          ))}
                        </div>
                      </td>
                      <td className="px-5 py-4 align-top">
                        {latest ? (
                          <div className="min-w-[220px]">
                            <p className="text-sm font-semibold text-white">{latest.name} | {latest.symbol}</p>
                            <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                              {modeLabel(latest.pageMode)} | {latest.launchPattern ?? "No pattern"}
                            </p>
                            <p className="mt-1 text-xs font-semibold text-slate-300">
                              {latest.risk.toUpperCase()} | {launchAgeLabel(latest.ageMinutes)}
                            </p>
                            <p className="mt-2 text-xs text-slate-500">Updated {relativeTimeLabel(latest.refreshedAt)}</p>
                          </div>
                        ) : (
                          <span className="text-sm text-slate-500">No launch yet</span>
                        )}
                      </td>
                      <td className="px-5 py-4 text-right align-top">
                        <button
                          className="rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-4 py-2 text-xs font-bold uppercase tracking-[0.16em] text-[#93c5fd] transition hover:bg-[#3b82f6]/20"
                          onClick={() => setSelectedId(profile.id)}
                          type="button"
                        >
                          Unlock wallet
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="grid gap-4 p-4 lg:hidden">
            {filteredProfiles.map((profile) => {
              const latest = profile.latestLaunches[0];
              return (
                <button
                  key={profile.id}
                  className="rounded-[24px] border border-white/10 bg-white/[0.03] p-5 text-left transition hover:border-[#3b82f6]/20"
                  onClick={() => setSelectedId(profile.id)}
                  type="button"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#93c5fd]">
                      {walletKindLabel(profile)}
                    </span>
                    <span className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${operatorClasses(profile.operatorScore)}`}>
                      Score {profile.operatorScore}
                    </span>
                  </div>
                  <h3 className="mt-4 text-xl font-black tracking-[-0.04em] text-white">{profile.label}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{profile.summary}</p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Launches</p>
                      <p className="mt-2 text-lg font-semibold text-white">{profile.launches}</p>
                    </div>
                    <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Risky launches</p>
                      <p className="mt-2 text-lg font-semibold text-white">{profile.highRiskLaunches}</p>
                    </div>
                  </div>
                  <div className="mt-4 rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Funding trace</p>
                    <p className="mt-2 text-sm font-semibold text-white">{profile.fundingSource ?? "Hidden / unresolved"}</p>
                    <p className="mt-1 text-xs text-slate-400">{profile.confidence} | {profile.coverage}</p>
                  </div>
                  {latest ? (
                    <div className="mt-4 rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Latest launch</p>
                      <p className="mt-2 text-sm font-semibold text-white">{latest.name} | {latest.symbol}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                        {modeLabel(latest.pageMode)} | {latest.launchPattern ?? "No pattern"}
                      </p>
                    </div>
                  ) : null}
                </button>
              );
            })}
          </div>

          {!filteredProfiles.length ? (
            <div className="border-t border-white/10 px-5 py-10 text-center">
              <p className="text-lg font-semibold text-white">No operators match the current filters.</p>
              <p className="mt-3 text-sm leading-7 text-slate-400">
                Reset the board filters or run more token checks so the wallet graph can surface more launch operators.
              </p>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="mt-6 rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-8 text-center">
          <p className="text-lg font-semibold text-white">No launch wallets are tracked yet.</p>
          <p className="mt-3 text-sm leading-7 text-slate-400">
            Run more token checks and launch scans. Once the wallet graph resolves funding routes or linked wallet clusters, they will show up here like a feed.
          </p>
        </div>
      )}

      {selected ? (
        <div className="fixed inset-0 z-[80] grid place-items-center bg-[rgba(2,6,23,0.66)] p-4 backdrop-blur-[10px]">
          <div className="w-full max-w-3xl rounded-[30px] border border-[#3b82f6]/20 bg-[linear-gradient(180deg,rgba(8,19,35,0.98),rgba(5,12,24,0.98))] p-6 shadow-[0_30px_120px_rgba(2,6,23,0.6)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#93c5fd]">
                    {walletKindLabel(selected)}
                  </span>
                  <span className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${operatorClasses(selected.operatorScore)}`}>
                    Operator score {selected.operatorScore}
                  </span>
                  <span className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${statusClasses(selected.profileStatus)}`}>
                    {selected.profileStatus}
                  </span>
                </div>
                <h3 className="mt-4 text-3xl font-black tracking-[-0.05em] text-white">{selected.label}</h3>
                <p className="mt-2 text-sm text-slate-400">{selected.walletPreview}</p>
              </div>
              <button
                className="flex h-11 w-11 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-300 transition hover:border-[#3b82f6]/30 hover:text-white"
                onClick={() => setSelectedId(null)}
                type="button"
              >
                <AppIcon className="h-5 w-5" name="close" />
              </button>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-4">
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Tracked launches</p>
                <p className="mt-2 text-lg font-semibold text-white">{selected.launches}</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Risky launches</p>
                <p className="mt-2 text-lg font-semibold text-white">{selected.highRiskLaunches}</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Confidence</p>
                <p className="mt-2 text-lg font-semibold text-white">{selected.confidence}</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Funding route</p>
                <p className="mt-2 text-lg font-semibold text-white">{selected.fundingSource ?? "Hidden"}</p>
              </div>
            </div>

            <div className="mt-6 rounded-[26px] border border-white/10 bg-white/[0.03] p-5">
              <p className="text-sm leading-7 text-slate-300">{selected.premiumPrompt}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {selected.flags.slice(0, 4).map((flag) => (
                  <span
                    key={flag}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-300"
                  >
                    {flag}
                  </span>
                ))}
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <PremiumCheckoutButton
                  className="rounded-xl bg-[#3b82f6] px-5 py-3 text-center text-sm font-bold text-white"
                  label="Unlock with Premium"
                />
                <button
                  className="rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-bold text-slate-100"
                  onClick={() => setSelectedId(null)}
                  type="button"
                >
                  Maybe later
                </button>
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {selected.topMetrics.map((metric) => (
                <div key={metric.label} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{metric.label}</p>
                  <p className="mt-2 text-lg font-semibold text-white">{metric.value}</p>
                </div>
              ))}
            </div>

            <div className="mt-6 overflow-hidden rounded-[26px] border border-white/10">
              <div className="pointer-events-none select-none blur-[10px] opacity-40">
                <div className="grid gap-4 p-5 lg:grid-cols-2">
                  <div className="space-y-3">
                    {selected.profileSignals.map((signal) => (
                      <div key={signal.label} className={`rounded-2xl border px-4 py-3 ${signalTone(signal.tone)}`}>
                        <p className="text-[10px] font-bold uppercase tracking-[0.18em]">{signal.label}</p>
                        <p className="mt-2 text-lg font-semibold">{signal.value}</p>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-3">
                    {selected.latestLaunches.map((launch) => (
                      <div key={launch.id} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                        <p className="text-sm font-semibold text-white">{launch.name}</p>
                        <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                          {launch.symbol} | {launch.launchPattern ?? "No pattern"}
                        </p>
                        <p className="mt-2 text-sm text-slate-300">{launch.risk.toUpperCase()} | {launchAgeLabel(launch.ageMinutes)}</p>
                        <p className="mt-1 text-xs text-slate-500">Updated {relativeTimeLabel(launch.refreshedAt)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="border-t border-white/10 px-5 py-4 text-center text-xs font-bold uppercase tracking-[0.22em] text-[#93c5fd]">
                Premium unlocks full wallet history, linked addresses, launch archive, and cluster evidence
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
