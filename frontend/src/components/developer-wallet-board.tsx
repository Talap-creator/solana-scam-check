"use client";

import { useMemo, useState } from "react";
import { AppIcon } from "@/components/app-icon";
import { APP_TELEGRAM_URL } from "@/lib/plans";
import type { DeveloperLeadProfile } from "@/lib/developer-leads";

type DeveloperWalletBoardProps = {
  profiles: DeveloperLeadProfile[];
};

function riskTone(value: number) {
  if (value >= 75) return "border-rose-500/20 bg-rose-500/10 text-rose-200";
  if (value >= 50) return "border-orange-400/20 bg-orange-400/10 text-orange-100";
  if (value >= 25) return "border-amber-400/20 bg-amber-400/10 text-amber-100";
  return "border-sky-400/20 bg-sky-400/10 text-sky-100";
}

function modeLabel(value: DeveloperLeadProfile["latestLaunches"][number]["pageMode"]) {
  if (value === "early_launch") return "Early launch";
  if (value === "early_market") return "Early market";
  return "Mature";
}

export function DeveloperWalletBoard({ profiles }: DeveloperWalletBoardProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selected = useMemo(
    () => profiles.find((item) => item.id === selectedId) ?? null,
    [profiles, selectedId],
  );

  return (
    <>
      {profiles.length ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {profiles.map((profile) => (
            <button
              key={profile.id}
              className="rounded-[26px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-6 text-left transition hover:border-[#3b82f6]/25 hover:bg-[linear-gradient(180deg,rgba(11,23,42,0.98),rgba(8,14,26,0.98))]"
              onClick={() => setSelectedId(profile.id)}
              type="button"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#93c5fd]">
                      {profile.kind === "wallet" ? "Launch wallet" : "Signal cluster"}
                    </span>
                    {profile.unresolved ? (
                      <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-300">
                        Redacted
                      </span>
                    ) : null}
                  </div>
                  <h2 className="mt-4 text-2xl font-black tracking-[-0.05em] text-white">{profile.label}</h2>
                  <p className="mt-2 text-sm leading-7 text-slate-400">{profile.summary}</p>
                </div>
                <div className={`rounded-2xl border px-4 py-3 text-right ${riskTone(profile.avgRugProbability)}`}>
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] opacity-75">Avg rug risk</p>
                  <p className="mt-2 text-2xl font-black">{profile.avgRugProbability}%</p>
                </div>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Tracked launches</p>
                  <p className="mt-2 text-lg font-semibold text-white">{profile.launches}</p>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Trade caution</p>
                  <p className="mt-2 text-lg font-semibold text-white">{profile.avgTradeCaution}</p>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Confidence</p>
                  <p className="mt-2 text-lg font-semibold text-white">{profile.confidence}</p>
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                {profile.flags.map((flag) => (
                  <span key={flag} className="rounded-full border border-white/10 bg-white/6 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-300">
                    {flag}
                  </span>
                ))}
              </div>

              <div className="mt-5 border-t border-white/10 pt-5">
                <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-slate-500">Latest launches</p>
                <div className="mt-3 grid gap-3">
                  {profile.latestLaunches.slice(0, 2).map((launch) => (
                    <div key={launch.id} className="flex items-center justify-between gap-3 rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{launch.name}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                          {launch.symbol} · {modeLabel(launch.pageMode)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#93c5fd]">
                          {launch.launchPattern ?? "No pattern"}
                        </p>
                        <p className="mt-1 text-sm text-slate-300">{launch.risk.toUpperCase()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-8 text-center">
          <p className="text-lg font-semibold text-white">No developer-linked launch wallets are tracked yet.</p>
          <p className="mt-3 text-sm leading-7 text-slate-400">
            Run more token checks and launch scans. Once the wallet graph picks up shared funding routes or linked launch clusters, they will appear here.
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
                    {selected.kind === "wallet" ? "Launch wallet" : "Signal cluster"}
                  </span>
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-300">
                    Premium detail
                  </span>
                </div>
                <h3 className="mt-4 text-3xl font-black tracking-[-0.05em] text-white">{selected.label}</h3>
                <p className="mt-2 text-sm text-slate-400">{selected.walletPreview}</p>
              </div>
              <button
                className="rounded-full border border-white/10 bg-white/5 p-3 text-slate-300 transition hover:border-[#3b82f6]/30 hover:text-white"
                onClick={() => setSelectedId(null)}
                type="button"
              >
                <AppIcon className="h-5 w-5" name="info" />
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
                <a
                  className="rounded-xl bg-[#3b82f6] px-5 py-3 text-center text-sm font-bold text-white"
                  href={APP_TELEGRAM_URL}
                  rel="noreferrer"
                  target="_blank"
                >
                  Write Mr Talap
                </a>
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
                        {launch.symbol} · {launch.launchPattern ?? "No pattern"}
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
