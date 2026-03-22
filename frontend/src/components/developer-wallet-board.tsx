"use client";

import { useMemo, useState } from "react";
import { AppIcon } from "@/components/app-icon";
import { PremiumCheckoutButton } from "@/components/premium-checkout-button";
import type { DeveloperLeadProfile } from "@/lib/developer-leads";

type DeveloperWalletBoardProps = {
  profiles: DeveloperLeadProfile[];
};

function riskBadge(score: number) {
  if (score >= 75) return "border-rose-500/20 bg-rose-500/10 text-rose-200";
  if (score >= 50) return "border-orange-400/20 bg-orange-400/10 text-orange-100";
  if (score >= 25) return "border-amber-400/20 bg-amber-400/10 text-amber-100";
  return "border-sky-400/20 bg-sky-400/10 text-sky-100";
}

function cautionTone(value: string) {
  if (/avoid/i.test(value)) return "text-rose-300";
  if (/high/i.test(value)) return "text-orange-200";
  if (/moderate/i.test(value)) return "text-amber-200";
  return "text-emerald-200";
}

function modeLabel(value: DeveloperLeadProfile["latestLaunches"][number]["pageMode"]) {
  if (value === "early_launch") return "Early launch";
  if (value === "early_market") return "Early market";
  return "Mature";
}

function walletKindLabel(profile: DeveloperLeadProfile) {
  if (profile.kind === "wallet") {
    return "Launch wallet";
  }
  return "Wallet cluster";
}

function latestLaunchLabel(profile: DeveloperLeadProfile) {
  const latest = profile.latestLaunches[0];
  if (!latest) {
    return "No launch yet";
  }
  return `${latest.name} | ${latest.symbol}`;
}

export function DeveloperWalletBoard({ profiles }: DeveloperWalletBoardProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selected = useMemo(
    () => profiles.find((item) => item.id === selectedId) ?? null,
    [profiles, selectedId],
  );

  const walletCount = profiles.filter((item) => item.kind === "wallet").length;
  const flaggedCount = profiles.filter((item) => item.avgRugProbability >= 50).length;
  const avgRug = profiles.length
    ? Math.round(profiles.reduce((total, item) => total + item.avgRugProbability, 0) / profiles.length)
    : 0;

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-3">
        <article className="rounded-[24px] border border-white/10 bg-[#020617] px-5 py-5">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Tracked wallets</p>
          <p className="mt-3 text-3xl font-black text-white">{walletCount}</p>
          <p className="mt-2 text-sm text-slate-400">Launch wallets resolved from recent token checks.</p>
        </article>
        <article className="rounded-[24px] border border-white/10 bg-[#020617] px-5 py-5">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">High-risk operators</p>
          <p className="mt-3 text-3xl font-black text-white">{flaggedCount}</p>
          <p className="mt-2 text-sm text-slate-400">Wallets or clusters already tied to repeated risky launches.</p>
        </article>
        <article className="rounded-[24px] border border-white/10 bg-[#020617] px-5 py-5">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Average rug risk</p>
          <p className="mt-3 text-3xl font-black text-white">{avgRug}%</p>
          <p className="mt-2 text-sm text-slate-400">Across the currently surfaced launch wallets and clusters.</p>
        </article>
      </div>

      {profiles.length ? (
        <>
          <div className="mt-6 overflow-hidden rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))]">
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[#93c5fd]">
                  Launch wallet board
                </p>
                <p className="mt-2 text-sm text-slate-400">
                  Wallets and linked launch clusters ranked like a feed, not a marketing page.
                </p>
              </div>
              <span className="hidden rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#93c5fd] sm:inline-flex">
                Updated from recent token reports
              </span>
            </div>

            <div className="hidden overflow-x-auto lg:block">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-white/8 bg-white/[0.02] text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">
                  <tr>
                    <th className="px-5 py-4">Wallet</th>
                    <th className="px-5 py-4">Launches</th>
                    <th className="px-5 py-4">Avg rug risk</th>
                    <th className="px-5 py-4">Trade caution</th>
                    <th className="px-5 py-4">Confidence</th>
                    <th className="px-5 py-4">Latest launch</th>
                    <th className="px-5 py-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/8">
                  {profiles.map((profile) => {
                    const latest = profile.latestLaunches[0];
                    return (
                      <tr
                        key={profile.id}
                        className="transition hover:bg-white/[0.03]"
                      >
                        <td className="px-5 py-4 align-top">
                          <div className="min-w-[230px]">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#93c5fd]">
                                {walletKindLabel(profile)}
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
                          </div>
                        </td>
                        <td className="px-5 py-4 align-top text-white">{profile.launches}</td>
                        <td className="px-5 py-4 align-top">
                          <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-bold ${riskBadge(profile.avgRugProbability)}`}>
                            {profile.avgRugProbability}%
                          </span>
                        </td>
                        <td className={`px-5 py-4 align-top text-sm font-semibold ${cautionTone(profile.avgTradeCaution)}`}>
                          {profile.avgTradeCaution}
                        </td>
                        <td className="px-5 py-4 align-top text-sm text-slate-300">{profile.confidence}</td>
                        <td className="px-5 py-4 align-top">
                          {latest ? (
                            <div className="min-w-[220px]">
                              <p className="text-sm font-semibold text-white">{latestLaunchLabel(profile)}</p>
                              <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                                {modeLabel(latest.pageMode)} | {latest.launchPattern ?? "No pattern"}
                              </p>
                              <p className="mt-1 text-xs font-semibold text-slate-300">{latest.risk.toUpperCase()}</p>
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
              {profiles.map((profile) => {
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
                      <span className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${riskBadge(profile.avgRugProbability)}`}>
                        {profile.avgRugProbability}% risk
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
                        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Trade caution</p>
                        <p className={`mt-2 text-lg font-semibold ${cautionTone(profile.avgTradeCaution)}`}>{profile.avgTradeCaution}</p>
                      </div>
                    </div>
                    {latest ? (
                      <div className="mt-4 rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Latest launch</p>
                        <p className="mt-2 text-sm font-semibold text-white">{latestLaunchLabel(profile)}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                          {modeLabel(latest.pageMode)} | {latest.launchPattern ?? "No pattern"}
                        </p>
                      </div>
                    ) : null}
                  </button>
                );
              })}
            </div>
          </div>
        </>
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
          <div className="w-full max-w-2xl rounded-[30px] border border-[#3b82f6]/20 bg-[linear-gradient(180deg,rgba(8,19,35,0.98),rgba(5,12,24,0.98))] p-6 shadow-[0_30px_120px_rgba(2,6,23,0.6)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#93c5fd]">
                    {walletKindLabel(selected)}
                  </span>
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-300">
                    Premium detail
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

            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Tracked launches</p>
                <p className="mt-2 text-lg font-semibold text-white">{selected.launches}</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Avg rug risk</p>
                <p className="mt-2 text-lg font-semibold text-white">{selected.avgRugProbability}%</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Confidence</p>
                <p className="mt-2 text-lg font-semibold text-white">{selected.confidence}</p>
              </div>
            </div>

            <div className="mt-6 rounded-[26px] border border-white/10 bg-[rgba(255,255,255,0.03)] p-5">
              <p className="text-sm leading-7 text-slate-300">{selected.premiumPrompt}</p>
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

            <div className="mt-6 overflow-hidden rounded-[26px] border border-white/10">
              <div className="pointer-events-none select-none blur-[10px] opacity-40">
                <div className="grid gap-4 p-5 md:grid-cols-2">
                  {selected.latestLaunches.map((launch) => (
                    <div key={launch.id} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                      <p className="text-sm font-semibold text-white">{launch.name}</p>
                      <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                        {launch.symbol} | {launch.launchPattern ?? "No pattern"}
                      </p>
                      <p className="mt-2 text-sm text-slate-300">{launch.risk.toUpperCase()}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="border-t border-white/10 px-5 py-4 text-center text-xs font-bold uppercase tracking-[0.22em] text-[#93c5fd]">
                Full wallet history is premium
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
