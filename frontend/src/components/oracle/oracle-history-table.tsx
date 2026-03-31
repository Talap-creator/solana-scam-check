"use client";

import type { OraclePublishEvent } from "@/lib/api";

function shortenAddress(addr: string) {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export function OracleHistoryTable({ events }: { events: OraclePublishEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-4 text-center text-sm text-slate-400 sm:p-8">
        No publish events yet. Start the agent to begin scoring.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)]">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[rgba(59,130,246,0.12)] text-left text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
            <th className="px-3 py-3 sm:px-6 sm:py-4">Time</th>
            <th className="px-3 py-3 sm:px-6 sm:py-4">Token</th>
            <th className="px-3 py-3 sm:px-6 sm:py-4">Score</th>
            <th className="px-3 py-3 sm:px-6 sm:py-4">Risk</th>
            <th className="px-3 py-3 sm:px-6 sm:py-4">Status</th>
            <th className="px-3 py-3 sm:px-6 sm:py-4">TX</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr
              key={e.id}
              className="border-b border-[rgba(59,130,246,0.06)] transition-colors hover:bg-[rgba(59,130,246,0.04)]"
            >
              <td className="px-3 py-2 sm:px-6 sm:py-3 text-xs text-slate-400">
                {new Date(e.published_at).toLocaleString()}
              </td>
              <td className="px-3 py-2 sm:px-6 sm:py-3 font-mono text-slate-200">
                {shortenAddress(e.token_address)}
              </td>
              <td className="px-3 py-2 sm:px-6 sm:py-3 font-bold text-slate-100">{e.score}</td>
              <td className="px-3 py-2 sm:px-6 sm:py-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  {e.risk_level}
                </span>
              </td>
              <td className="px-3 py-2 sm:px-6 sm:py-3">
                <span
                  className={`inline-block rounded-full px-2 py-0.5 text-xs font-bold ${
                    e.status === "published"
                      ? "bg-emerald-400/10 text-emerald-400"
                      : "bg-rose-400/10 text-rose-400"
                  }`}
                >
                  {e.status}
                </span>
              </td>
              <td className="px-3 py-2 sm:px-6 sm:py-3">
                {e.tx_signature ? (
                  <a
                    href={`https://explorer.solana.com/tx/${e.tx_signature}?cluster=devnet`}
                    target="_blank"
                    rel="noreferrer"
                    className="font-mono text-xs text-[#60a5fa] hover:underline"
                  >
                    {e.tx_signature.slice(0, 12)}...
                  </a>
                ) : (
                  <span className="text-xs text-slate-500">
                    {e.error_message ?? "--"}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
