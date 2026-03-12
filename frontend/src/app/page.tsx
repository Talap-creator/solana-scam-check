import Link from "next/link";
import { AnimatedScanPreview } from "@/components/animated-scan-preview";
import { AppIcon } from "@/components/app-icon";
import { SearchCheckForm } from "@/components/search-check-form";
import { getChecks } from "@/lib/api";

const engineCards = [
  {
    title: "Contract Control",
    copy: "Ownership analysis and permission monitoring for potential backdoors.",
    icon: "control",
  },
  {
    title: "Token Distribution",
    copy: "Whale tracking and holder concentration alerts to prevent dumping.",
    icon: "holders",
  },
  {
    title: "Liquidity Stability",
    copy: "LP burn status, lock duration metrics, and depth analysis.",
    icon: "drop",
  },
  {
    title: "Behaviour Signals",
    copy: "MEV activity monitoring and bot pattern recognition in real-time.",
    icon: "radar",
  },
  {
    title: "Market Maturity",
    copy: "Volume consistency and historical trading pattern validation.",
    icon: "chart",
  },
] as const;

const audienceCards = [
  ["Traders", "Automated rug-check tools to protect your daily swaps.", "trending"],
  ["Wallets", "Integrate our risk scores directly into your user's signing experience.", "wallet"],
  ["Launchpads", "Whitelist protocols based on verifiable onchain health metrics.", "rocket"],
  ["Researchers", "High-fidelity data for deep forensic onchain investigations.", "analytics"],
] as const;

const developerBullets = [
  "WebSocket streams for new launches",
  "Historical security data archive",
  "Batch risk assessment endpoints",
] as const;

function BrandMark() {
  return <AppIcon className="h-8 w-8 text-[#3b82f6]" name="shield" />;
}

function riskTone(score: number) {
  if (score >= 75) return "bg-red-500/10 text-red-500";
  if (score >= 45) return "bg-yellow-500/10 text-yellow-500";
  return "bg-green-500/10 text-green-500";
}

function riskDot(score: number) {
  if (score >= 75) return "bg-red-500";
  if (score >= 45) return "bg-yellow-500";
  return "bg-green-500";
}

export default async function Home() {
  const checks = await getChecks();
  const feedPreview = checks.slice(0, 3);
  const previewItems = checks.slice(0, 4).map((item) => ({
    displayName: item.displayName,
    status: item.status,
  }));

  return (
    <main className="min-h-screen bg-[#020617] text-slate-100 antialiased">
      <div className="relative flex min-h-screen w-full flex-col overflow-x-hidden">
        <header className="sticky top-0 z-50 w-full border-b border-[rgba(59,130,246,0.1)] bg-[rgba(2,6,23,0.82)] backdrop-blur-md">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center gap-8">
                <div className="flex items-center gap-2 text-[#3b82f6]">
                  <BrandMark />
                  <h2 className="text-xl font-bold tracking-tight text-slate-100">SolanaTrust</h2>
                </div>
                <nav className="hidden items-center gap-6 md:flex">
                  <a className="text-sm font-medium transition-colors hover:text-[#3b82f6]" href="#engine">
                    Intelligence
                  </a>
                  <Link className="text-sm font-medium transition-colors hover:text-[#3b82f6]" href="/coins">
                    Live Feed
                  </Link>
                  <a className="text-sm font-medium transition-colors hover:text-[#3b82f6]" href="#developers">
                    Developers
                  </a>
                  <a className="text-sm font-medium transition-colors hover:text-[#3b82f6]" href="#pricing">
                    Pricing
                  </a>
                </nav>
              </div>
              <div className="flex items-center gap-4">
                <Link className="rounded-lg bg-[#3b82f6] px-4 py-2 text-sm font-bold text-white transition-all hover:brightness-110" href="/login">
                  Log In
                </Link>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-grow">
          <section className="relative overflow-hidden py-20 lg:py-32">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.05),transparent)]" />
            <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="grid items-center gap-12 lg:grid-cols-2">
                <div className="flex flex-col gap-8">
                  <div className="space-y-4">
                    <span className="inline-flex items-center rounded-full bg-[#3b82f6]/10 px-3 py-1 text-xs font-medium text-[#3b82f6] ring-1 ring-inset ring-[#3b82f6]/20">
                      Institutional Grade Analytics
                    </span>
                    <h1 className="text-5xl font-black leading-tight tracking-tighter text-slate-100 lg:text-7xl">
                      Solana Onchain <span className="text-[#3b82f6]">Risk Intelligence</span>
                    </h1>
                    <p className="max-w-xl text-lg text-slate-400">
                      Real-time security analytics and risk scoring for the Solana ecosystem. Identify rugs, honey pots, and malicious contracts before they strike.
                    </p>
                  </div>
                  <div className="relative max-w-xl">
                    <SearchCheckForm
                      leadingIcon
                      placeholder="Enter token mint address (e.g. EPjFW...)"
                      submitLabel="Analyze"
                      tokenOnly
                      variant="landing"
                    />
                  </div>
                </div>

                <div className="hidden lg:block">
                  <div className="relative h-[400px] w-full overflow-hidden rounded-2xl border border-[#3b82f6]/20 bg-[#3b82f6]/5 p-4 shadow-[0_0_20px_rgba(59,130,246,0.1)]">
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_52%_42%,rgba(59,130,246,0.12),transparent_18%),radial-gradient(circle_at_55%_60%,rgba(16,185,129,0.08),transparent_16%)]" />
                    <div className="relative flex h-full flex-col justify-between rounded-xl bg-[linear-gradient(135deg,#0f172a_0%,#020617_100%)] p-6">
                      <div className="flex gap-2">
                        <div className="h-3 w-3 rounded-full bg-red-500/50" />
                        <div className="h-3 w-3 rounded-full bg-yellow-500/50" />
                        <div className="h-3 w-3 rounded-full bg-[#3b82f6]/50" />
                      </div>
                      <AnimatedScanPreview items={previewItems} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="bg-[#3b82f6]/5 py-20" id="engine">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="mb-16 text-center">
                <h2 className="mb-4 text-3xl font-bold tracking-tight text-slate-100">Risk Intelligence Engine</h2>
                <p className="text-slate-400">Five pillars of automated security auditing</p>
              </div>
              <div className="grid grid-cols-1 gap-6 md:grid-cols-3 lg:grid-cols-5">
                {engineCards.map((card) => (
                  <article key={card.title} className="group relative rounded-xl border border-[#3b82f6]/10 bg-[#020617] p-6 transition-all hover:border-[#3b82f6]/40 hover:shadow-lg hover:shadow-[#3b82f6]/5">
                    <AppIcon className="mb-4 h-10 w-10 text-[#3b82f6]" name={card.icon} />
                    <h3 className="mb-2 text-lg font-bold">{card.title}</h3>
                    <p className="text-sm leading-relaxed text-slate-400">{card.copy}</p>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section className="py-20">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-center">
                <div>
                  <h2 className="text-3xl font-bold tracking-tight text-slate-100">Live Solana Launch Feed</h2>
                  <p className="mt-2 text-slate-400">Latest token launches monitored by SolanaTrust</p>
                </div>
                <Link className="flex items-center gap-2 rounded-lg border border-[#3b82f6]/20 px-4 py-2 text-sm font-semibold text-[#3b82f6] hover:bg-[#3b82f6]/10" href="/coins">
                  <AppIcon className="h-4 w-4" name="filter" />
                  Filters
                </Link>
              </div>
              <div className="overflow-x-auto rounded-xl border border-[#3b82f6]/10 bg-[#020617]">
                <table className="w-full text-left text-sm">
                  <thead className="bg-[#3b82f6]/5 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    <tr>
                      <th className="px-6 py-4">Token Name</th>
                      <th className="px-6 py-4">Launch Time</th>
                      <th className="px-6 py-4">Liquidity</th>
                      <th className="px-6 py-4">Risk Score</th>
                      <th className="px-6 py-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#3b82f6]/5">
                    {feedPreview.map((item) => (
                      <tr key={item.id} className="transition-colors hover:bg-[#3b82f6]/5">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#3b82f6]/20 font-bold text-[#3b82f6]">
                              {item.displayName.slice(0, 1)}
                            </div>
                            <span className="font-medium text-slate-100">{item.displayName}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-slate-400">{item.refreshedAt}</td>
                        <td className="px-6 py-4 text-slate-400">{item.liquidity}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-bold ${riskTone(item.score)}`}>
                            <span className={`h-1.5 w-1.5 rounded-full ${riskDot(item.score)}`} />
                            {item.score}/100
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <Link className="text-[#3b82f6] hover:underline" href={`/report/${item.entityType}/${item.id}`}>
                            View Audit
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <section className="bg-[#3b82f6]/5 py-20">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="mb-16 text-center">
                <h2 className="mb-4 text-3xl font-bold tracking-tight text-slate-100">Who is SolanaTrust for?</h2>
                <p className="text-slate-400">Scalable security intelligence for every stakeholder</p>
              </div>
              <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
                {audienceCards.map(([title, copy, icon]) => (
                  <article key={title} className="flex flex-col items-center rounded-2xl border border-[#3b82f6]/10 bg-[#020617] p-8 text-center">
                    <div className="mb-6 flex size-16 items-center justify-center rounded-full bg-[#3b82f6]/10">
                      <AppIcon className="h-8 w-8 text-[#3b82f6]" name={icon} />
                    </div>
                    <h3 className="mb-3 text-xl font-bold">{title}</h3>
                    <p className="text-sm text-slate-400">{copy}</p>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section className="py-24" id="developers">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="grid items-center gap-16 lg:grid-cols-2">
                <div className="space-y-6">
                  <h2 className="text-4xl font-bold tracking-tight text-slate-100">Built for Developers</h2>
                  <p className="text-lg text-slate-400">
                    Integrate SolanaTrust into your project with just a few lines of code. Our low-latency API provides real-time risk assessments for any Solana mint address.
                  </p>
                  <ul className="space-y-4">
                    {developerBullets.map((bullet) => (
                      <li key={bullet} className="flex items-center gap-3">
                        <AppIcon className="h-5 w-5 text-[#3b82f6]" name="check" />
                        <span>{bullet}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-4 inline-flex rounded-lg border border-[#3b82f6]/30 bg-[#3b82f6]/10 px-6 py-3 font-bold text-[#3b82f6]">
                    In development
                  </div>
                </div>
                <div className="group relative">
                  <div className="absolute -inset-1 rounded-xl bg-[#3b82f6]/20 opacity-30 blur transition duration-1000 group-hover:opacity-50" />
                  <div className="relative overflow-hidden rounded-xl bg-[#0a1120] p-6 text-sm font-mono leading-relaxed text-slate-300">
                    <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-2">
                      <span className="text-xs text-slate-500">risk_assessment.js</span>
                      <AppIcon className="h-4 w-4 text-slate-500" name="copy" />
                    </div>
                    <pre><code>{`const trust = require('@solanatrust/sdk');

const client = new trust.Client(process.env.ST_KEY);

async function checkRisk(mintAddress) {
  const score = await client.getRiskScore(mintAddress);

  if (score.riskLevel === 'CRITICAL') {
    return blockTransaction();
  }

  console.log(\`Risk Score: \${score.total}\`);
}`}</code></pre>
                  </div>
                  <div className="absolute inset-0 grid place-items-center rounded-xl bg-[rgba(2,6,23,0.52)] backdrop-blur-[6px]">
                    <div className="rounded-full border border-[#3b82f6]/30 bg-[#3b82f6]/10 px-5 py-2 text-sm font-bold text-[#93c5fd]">
                      In development
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </main>

        <footer className="border-t border-[#3b82f6]/10 py-12">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mb-12 grid gap-12 md:grid-cols-4">
              <div className="col-span-2">
                <div className="mb-6 flex items-center gap-2 text-[#3b82f6]">
                  <BrandMark />
                  <h2 className="text-lg font-bold tracking-tight text-slate-100">SolanaTrust</h2>
                </div>
                <p className="mb-6 text-slate-400">
                  The leading provider of onchain risk intelligence for the Solana ecosystem. Powered by decentralized data and institutional expertise.
                </p>
                <div className="flex gap-4">
                  <AppIcon className="h-5 w-5 text-slate-400" name="share" />
                  <AppIcon className="h-5 w-5 text-slate-400" name="mail" />
                  <AppIcon className="h-5 w-5 text-slate-400" name="rss" />
                </div>
              </div>
              <div>
                <h3 className="mb-6 font-bold">Product</h3>
                <ul className="space-y-4 text-sm text-slate-400">
                  <li>Risk Engine</li>
                  <li>API Reference</li>
                  <li>Live Feed</li>
                  <li id="pricing">Pricing</li>
                </ul>
              </div>
              <div>
                <h3 className="mb-6 font-bold">Resources</h3>
                <ul className="space-y-4 text-sm text-slate-400">
                  <li>Security Whitepaper</li>
                  <li>Governance</li>
                  <li>Privacy Policy</li>
                  <li>Terms of Service</li>
                </ul>
              </div>
            </div>
            <div className="border-t border-[#3b82f6]/5 pt-8 text-center text-xs text-slate-500">
              Copyright 2026 SolanaTrust Intelligence Systems. All data provided as-is for informational purposes.
            </div>
          </div>
        </footer>
      </div>
    </main>
  );
}
