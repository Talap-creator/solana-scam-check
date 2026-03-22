import Link from "next/link";
import { AppIcon } from "@/components/app-icon";
import { getServerApiBaseUrl } from "@/lib/api-base";
import { APP_TELEGRAM_URL } from "@/lib/plans";

const endpoints = [
  {
    method: "POST",
    path: "/api/v1/check/token",
    title: "Token Risk Checker",
    copy: "Create a token report for a Solana mint address.",
  },
  {
    method: "POST",
    path: "/api/v1/check/wallet",
    title: "Wallet Risk Checker",
    copy: "Score a wallet address for linked flags, launch-dump patterns, and suspicious history.",
  },
  {
    method: "POST",
    path: "/api/v1/check/project",
    title: "Project Checker",
    copy: "Scan a project domain or URL and map project-level risk signals.",
  },
  {
    method: "GET",
    path: "/api/v1/feed/launches",
    title: "Launch Feed API",
    copy: "Read live launch rows with rug probability, trade caution, and launch pattern context.",
  },
  {
    method: "POST",
    path: "/api/v1/recheck/{entity_type}/{entity_id}",
    title: "Recheck API",
    copy: "Refresh an existing token, wallet, or project report.",
  },
] as const;

const payloadExamples = {
  token: `{
  "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
}`,
  wallet: `{
  "address": "8PX1DbLyJQzY63K5kTz2S88xJ5UQh1dBnmfV91rYx4cR"
}`,
  project: `{
  "query": "https://exampleproject.io"
}`,
} as const;

export default function DevelopersPage() {
  const baseUrl = getServerApiBaseUrl();

  return (
    <main className="min-h-screen bg-[#020617] text-slate-100">
      <div className="relative flex min-h-screen flex-col overflow-x-hidden">
        <header className="sticky top-0 z-50 border-b border-[rgba(59,130,246,0.12)] bg-[rgba(2,6,23,0.84)] backdrop-blur-md">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
            <Link className="flex items-center gap-3 text-[#3b82f6]" href="/">
              <AppIcon className="h-8 w-8" name="shield" />
              <span className="text-xl font-bold tracking-tight text-slate-100">SolanaTrust</span>
            </Link>
            <div className="flex items-center gap-3">
              <Link className="rounded-lg border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-4 py-2 text-sm font-bold text-[#93c5fd]" href="/coins">
                Launch Feed
              </Link>
              <a
                className="rounded-lg bg-[#3b82f6] px-4 py-2 text-sm font-bold text-white"
                href={APP_TELEGRAM_URL}
                rel="noreferrer"
                target="_blank"
              >
                Telegram
              </a>
            </div>
          </div>
        </header>

        <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-10 px-4 py-10 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[#3b82f6]/12 bg-[linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-8">
            <span className="inline-flex rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-4 py-1 text-xs font-bold uppercase tracking-[0.24em] text-[#93c5fd]">
              Developer API
            </span>
            <h1 className="mt-5 text-4xl font-black tracking-[-0.05em] text-white sm:text-5xl">
              Token, Wallet, Project, and Launch Feed endpoints
            </h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-slate-400">
              Use SolanaTrust as a risk layer for wallets, launchpads, dashboards, and internal analyst tools.
              The API already supports token checks, wallet risk checks, project scans, launch feed reads, and rechecks.
            </p>
            <div className="mt-8 grid gap-4 md:grid-cols-[minmax(0,1fr)_260px]">
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-5">
                <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">Base URL</p>
                <code className="mt-3 block break-all rounded-xl border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-4 py-3 text-sm text-[#bfdbfe]">
                  {baseUrl}
                </code>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-5">
                <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">Current access</p>
                <p className="mt-3 text-sm leading-7 text-slate-300">
                  No separate API key flow yet. Public endpoints are live now, and premium/API-key gating can be added on top later.
                </p>
              </div>
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            {endpoints.map((endpoint) => (
              <article
                key={endpoint.path}
                className="rounded-[24px] border border-[#3b82f6]/12 bg-[linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-6"
              >
                <div className="flex items-center gap-3">
                  <span className={`rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-[0.2em] ${endpoint.method === "GET" ? "border border-emerald-500/20 bg-emerald-500/10 text-emerald-300" : "border border-[#3b82f6]/20 bg-[#3b82f6]/10 text-[#93c5fd]"}`}>
                    {endpoint.method}
                  </span>
                  <p className="text-sm font-bold text-white">{endpoint.title}</p>
                </div>
                <code className="mt-4 block rounded-xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-200">
                  {endpoint.path}
                </code>
                <p className="mt-4 text-sm leading-7 text-slate-400">{endpoint.copy}</p>
              </article>
            ))}
          </section>

          <section className="grid gap-6 lg:grid-cols-3">
            <article className="rounded-[24px] border border-[#3b82f6]/12 bg-[linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-6 lg:col-span-2">
              <div className="flex items-center gap-3">
                <AppIcon className="h-5 w-5 text-[#3b82f6]" name="code" />
                <h2 className="text-xl font-bold text-white">Example requests</h2>
              </div>
              <div className="mt-6 grid gap-4 md:grid-cols-3">
                <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Token</p>
                  <pre className="mt-3 overflow-x-auto text-xs leading-6 text-slate-300">{payloadExamples.token}</pre>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Wallet</p>
                  <pre className="mt-3 overflow-x-auto text-xs leading-6 text-slate-300">{payloadExamples.wallet}</pre>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Project</p>
                  <pre className="mt-3 overflow-x-auto text-xs leading-6 text-slate-300">{payloadExamples.project}</pre>
                </div>
              </div>
            </article>

            <article className="rounded-[24px] border border-[#3b82f6]/12 bg-[linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-6">
              <div className="flex items-center gap-3">
                <AppIcon className="h-5 w-5 text-[#3b82f6]" name="wallet" />
                <h2 className="text-xl font-bold text-white">What is already live</h2>
              </div>
              <ul className="mt-5 space-y-3 text-sm leading-7 text-slate-300">
                <li>Token risk reports</li>
                <li>Wallet risk checker</li>
                <li>Project scan endpoint</li>
                <li>Launch feed API</li>
                <li>Recheck API for refresh flows</li>
              </ul>
              <a
                className="mt-6 inline-flex rounded-lg border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-4 py-2 text-sm font-bold text-[#93c5fd]"
                href={APP_TELEGRAM_URL}
                rel="noreferrer"
                target="_blank"
              >
                Request integration support
              </a>
            </article>
          </section>
        </div>
      </div>
    </main>
  );
}
