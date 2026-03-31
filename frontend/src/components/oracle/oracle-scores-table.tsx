"use client";

import type { OracleScore } from "@/lib/api";

const riskColors: Record<string, string> = {
  low: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
  medium: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  high: "text-orange-400 bg-orange-400/10 border-orange-400/20",
  critical: "text-rose-400 bg-rose-400/10 border-rose-400/20",
};

function shortenAddress(addr: string) {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function OracleScoresTable({ scores }: { scores: OracleScore[] }) {
  if (scores.length === 0) {
    return (
      <div className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-4 text-center text-sm text-slate-400 sm:p-8">
        No tokens monitored yet. Add a token address above to start.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)]">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[rgba(59,130,246,0.12)] text-left text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
            <th className="px-3 py-3 sm:px-6 sm:py-4">Token</th>
            <th className="px-3 py-3 sm:px-6 sm:py-4">Score</th>
            <th className="px-3 py-3 sm:px-6 sm:py-4">Risk</th>
            <th className="px-3 py-3 sm:px-6 sm:py-4">Confidence</th>
            <th className="px-3 py-3 sm:px-6 sm:py-4">Last Published</th>
            <th className="px-3 py-3 sm:px-6 sm:py-4">TX</th>
          </tr>
        </thead>
        <tbody>
          {scores.map((s) => (
            <tr
              key={s.token_address}
              className="border-b border-[rgba(59,130,246,0.06)] transition-colors hover:bg-[rgba(59,130,246,0.04)]"
            >
              <td className="px-3 py-3 sm:px-6 sm:py-4">
                <div>
                  <span className="font-mono text-slate-200">
                    {shortenAddress(s.token_address)}
                  </span>
                  {s.display_name && (
                    <span className="ml-2 text-xs text-slate-400">{s.display_name}</span>
                  )}
                </div>
              </td>
              <td className="px-3 py-3 sm:px-6 sm:py-4">
                <div>
                  {s.score !== null ? (
                    <span className="font-[family:var(--font-display)] text-xl font-black">
                      {s.score}
                    </span>
                  ) : (
                    <span className="text-slate-500">--</span>
                  )}
                  {s.reasoning && (
                    <p className="mt-1 text-xs italic text-slate-400/70 leading-snug max-w-[260px]">
                      {s.reasoning}
                    </p>
                  )}
                </div>
              </td>
              <td className="px-3 py-3 sm:px-6 sm:py-4">
                {s.risk_level ? (
                  <span
                    className={`inline-block rounded-full border px-3 py-1 text-xs font-extrabold uppercase tracking-[0.14em] ${riskColors[s.risk_level] ?? "text-slate-400"}`}
                  >
                    {s.risk_level}
                  </span>
                ) : (
                  <span className="text-slate-500">--</span>
                )}
              </td>
              <td className="px-3 py-3 sm:px-6 sm:py-4 text-slate-300">
                {s.confidence !== null ? `${Math.round(s.confidence * 100)}%` : "--"}
              </td>
              <td className="px-3 py-3 sm:px-6 sm:py-4 text-slate-400">
                {s.last_published_at ? timeAgo(s.last_published_at) : "never"}
              </td>
              <td className="px-3 py-3 sm:px-6 sm:py-4">
                {s.tx_signature ? (
                  <a
                    href={`https://explorer.solana.com/tx/${s.tx_signature}?cluster=devnet`}
                    target="_blank"
                    rel="noreferrer"
                    className="font-mono text-xs text-[#60a5fa] hover:underline"
                  >
                    {s.tx_signature.slice(0, 12)}...
                  </a>
                ) : (
                  <span className="text-slate-500">--</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
