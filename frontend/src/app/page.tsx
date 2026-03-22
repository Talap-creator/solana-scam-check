import Link from "next/link";
import { AnimatedScanPreview } from "@/components/animated-scan-preview";
import { AppIcon } from "@/components/app-icon";
import { LandingHeaderAction } from "@/components/landing-header-action";
import { SearchCheckForm } from "@/components/search-check-form";
import { getChecks } from "@/lib/api";
import { APP_TELEGRAM_URL, getPlanMeta } from "@/lib/plans";

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
  "Shared funding routes across holder wallets",
  "Deployer-linked wallet clusters and supply control",
  "Seller pressure and coordinated exit timing",
] as const;

const developerIntelPreview = [
  {
    detail: "3 linked holder wallets resolve back into the same funding graph.",
    label: "Shared funding coverage",
    value: "42.0%",
  },
  {
    detail: "Linked cluster controls enough supply to move launch-time risk materially.",
    label: "Cluster supply control",
    value: "18.4%",
  },
  {
    detail: "Two tracked exit wallets now overlap inside the same compressed sell window.",
    label: "Exit wallet density",
    value: "2 wallets",
  },
  {
    detail: "Multi-hop funding traces still collapse back to one shared origin.",
    label: "Trace depth",
    value: "1.7 hops",
  },
] as const;

const teamMembers = [
  {
    name: "Kenzhebayev Talap",
    role: "CEO",
    icon: "groups" as const,
    accent: "linear-gradient(90deg, rgba(37, 99, 235, 0.25), rgba(56, 189, 248, 0.1))",
    focus: ["Product execution", "Partnerships", "Market growth"],
    bullets: [
      "Product Manager",
      "Ex BNB Chain Ambassador",
      "Ex Google Students Club Lead",
    ],
  },
  {
    name: "Berikuly Sabyr",
    role: "CTO",
    icon: "code" as const,
    accent: "linear-gradient(90deg, rgba(15, 118, 110, 0.25), rgba(34, 211, 238, 0.1))",
    focus: ["Python systems", "Rust services", "Web3 infrastructure"],
    bullets: [
      "3+ years of engineering experience",
      "Python, Rust, and Web3",
      "Production-focused backend and protocol delivery",
    ],
  },
] as const;

const pricingPlans = [
  {
    key: "free",
    features: [
      "5 token requests per day",
      "Early launch report preview",
      "Watchlist and basic dashboard access",
    ],
    ctaLabel: "Start free",
    ctaHref: "/register",
    featured: false,
  },
  {
    key: "pro",
    features: [
      "200 token requests per day",
      "Full token report unlock",
      "Priority Telegram support",
    ],
    ctaLabel: "Upgrade to Premium",
    ctaHref: APP_TELEGRAM_URL,
    featured: true,
  },
  {
    key: "enterprise",
    features: [
      "Unlimited team workflows",
      "Custom datasets and alerts",
      "Dedicated integration support",
    ],
    ctaLabel: "Write us",
    ctaHref: APP_TELEGRAM_URL,
    featured: false,
  },
] as const;

const pricingHighlights = [
  ["Live launch context", "Early launch radar, warnings, and staged confidence on every report."],
  ["Account-linked workflow", "Watchlist, usage limits, and dashboard state tied to your account."],
  ["Operator support", "Upgrade and enterprise onboarding go directly through Telegram."],
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
  const tokenChecks = checks.filter((item) => item.entityType === "token");
  const feedPreview = tokenChecks.slice(0, 3);
  const previewItems = tokenChecks.slice(0, 4).map((item) => ({
    displayName: item.displayName,
    status: item.status,
  }));
  const landingNav = [
    { href: "#engine", label: "Intelligence" },
    { href: "/coins", label: "Live Feed", external: false },
    { href: "/developers", label: "Developers", external: false },
    { href: "#team", label: "Team" },
    { href: "#pricing", label: "Pricing" },
  ] as const;

  return (
    <main className="min-h-screen bg-[#020617] text-slate-100 antialiased">
      <div className="relative flex min-h-screen w-full flex-col overflow-x-hidden">
        <header className="sticky top-0 z-50 w-full border-b border-[rgba(59,130,246,0.1)] bg-[rgba(2,6,23,0.82)] backdrop-blur-md">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex min-h-16 flex-wrap items-center justify-between gap-3 py-3 md:h-16 md:flex-nowrap md:py-0">
              <div className="flex items-center gap-8">
                <div className="flex items-center gap-2 text-[#3b82f6]">
                  <BrandMark />
                  <h2 className="text-xl font-bold tracking-tight text-slate-100">SolanaTrust</h2>
                </div>
                <nav className="hidden items-center gap-6 md:flex">
                  {landingNav.map((item) =>
                    item.href.startsWith("/") ? (
                      <Link key={item.href} className="text-sm font-medium transition-colors hover:text-[#3b82f6]" href={item.href}>
                        {item.label}
                      </Link>
                    ) : (
                      <a key={item.href} className="text-sm font-medium transition-colors hover:text-[#3b82f6]" href={item.href}>
                        {item.label}
                      </a>
                    ),
                  )}
                </nav>
              </div>
              <div className="flex items-center gap-4">
                <LandingHeaderAction />
              </div>
              <nav className="-mx-1 flex w-full gap-2 overflow-x-auto px-1 pb-1 md:hidden">
                {landingNav.map((item) =>
                  item.href.startsWith("/") ? (
                    <Link
                      key={item.href}
                      className="shrink-0 rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-2 text-xs font-bold uppercase tracking-[0.14em] text-[#93c5fd]"
                      href={item.href}
                    >
                      {item.label}
                    </Link>
                  ) : (
                    <a
                      key={item.href}
                      className="shrink-0 rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-2 text-xs font-bold uppercase tracking-[0.14em] text-[#93c5fd]"
                      href={item.href}
                    >
                      {item.label}
                    </a>
                  ),
                )}
              </nav>
            </div>
          </div>
        </header>

        <main className="flex-grow">
          <section className="relative overflow-hidden py-14 sm:py-20 lg:py-32">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.05),transparent)]" />
            <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="grid items-center gap-12 lg:grid-cols-2">
                <div className="flex flex-col gap-8">
                  <div className="space-y-4">
                    <span className="inline-flex items-center rounded-full bg-[#3b82f6]/10 px-3 py-1 text-xs font-medium text-[#3b82f6] ring-1 ring-inset ring-[#3b82f6]/20">
                      Institutional Grade Analytics
                    </span>
                    <h1 className="text-4xl font-black leading-tight tracking-tighter text-slate-100 sm:text-5xl lg:text-7xl">
                      Solana Onchain <span className="text-[#3b82f6]">Risk Intelligence</span>
                    </h1>
                    <p className="max-w-xl text-base text-slate-400 sm:text-lg">
                      Real-time security analytics and risk scoring for the Solana ecosystem. Identify rugs, honey pots, and malicious contracts before they strike.
                    </p>
                  </div>
                  <div className="relative max-w-xl">
                    <SearchCheckForm
                      leadingIcon
                      placeholder="Enter token mint, wallet, or project URL"
                      submitLabel="Analyze"
                      variant="landing"
                    />
                  </div>
                  <div className="lg:hidden">
                    <div className="relative overflow-hidden rounded-2xl border border-[#3b82f6]/20 bg-[#3b82f6]/5 p-4 shadow-[0_0_20px_rgba(59,130,246,0.08)]">
                      <div className="absolute inset-0 bg-[radial-gradient(circle_at_52%_42%,rgba(59,130,246,0.12),transparent_18%),radial-gradient(circle_at_55%_60%,rgba(16,185,129,0.08),transparent_16%)]" />
                      <div className="relative flex min-h-[240px] flex-col justify-between rounded-xl bg-[linear-gradient(135deg,#0f172a_0%,#020617_100%)] p-5">
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

          <section className="py-20" id="team">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="mb-14 text-center">
                <span className="inline-flex items-center rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-4 py-1 text-xs font-bold uppercase tracking-[0.2em] text-[#93c5fd]">
                  Core Team
                </span>
                <h2 className="mt-4 mb-4 text-3xl font-bold tracking-tight text-slate-100">Team</h2>
                <p className="mx-auto max-w-2xl text-slate-400">
                  Built by operators focused on product delivery, infrastructure, and Web3 execution.
                </p>
              </div>
              <div className="grid gap-6 lg:grid-cols-2">
                {teamMembers.map((member) => (
                  <article
                    key={member.name}
                    className={`overflow-hidden rounded-[28px] border border-[#3b82f6]/12 bg-[linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.96))] p-8 shadow-[0_24px_60px_rgba(2,6,23,0.18)]`}
                  >
                    <div className="-mx-8 -mt-8 mb-8 px-8 py-6" style={{ backgroundImage: member.accent }}>
                      <div className="flex items-start gap-4">
                        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#020617]/60 ring-1 ring-white/10">
                          <AppIcon className="h-7 w-7 text-[#60a5fa]" name={member.icon} />
                        </div>
                        <div>
                          <p className="text-xs font-bold uppercase tracking-[0.24em] text-[#93c5fd]">{member.role}</p>
                          <h3 className="mt-2 text-2xl font-bold tracking-tight text-slate-100">{member.name}</h3>
                        </div>
                      </div>
                    </div>
                    <div className="grid gap-4 md:grid-cols-[1fr_180px]">
                      <ul className="space-y-3">
                        {member.bullets.map((bullet) => (
                          <li key={bullet} className="flex items-start gap-3 text-sm leading-6 text-slate-300">
                            <AppIcon className="mt-0.5 h-5 w-5 shrink-0 text-[#3b82f6]" name="check" />
                            <span>{bullet}</span>
                          </li>
                        ))}
                      </ul>
                      <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Focus</p>
                        <div className="mt-4 space-y-3">
                          {member.focus.map((item) => (
                            <div
                              key={item}
                              className="rounded-xl border border-[#3b82f6]/12 bg-[rgba(59,130,246,0.06)] px-3 py-2 text-sm text-slate-200"
                            >
                              {item}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section className="bg-[#3b82f6]/5 py-20" id="pricing">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="mb-14 text-center">
                <span className="inline-flex items-center rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-4 py-1 text-xs font-bold uppercase tracking-[0.2em] text-[#93c5fd]">
                  Access Tiers
                </span>
                <h2 className="mt-4 mb-4 text-3xl font-bold tracking-tight text-slate-100">Pricing</h2>
                <p className="mx-auto max-w-2xl text-slate-400">
                  Simple access tiers for individual users, active traders, and enterprise teams.
                </p>
              </div>
              <div className="mb-10 grid gap-4 lg:grid-cols-3">
                {pricingHighlights.map(([title, copy]) => (
                  <article
                    key={title}
                    className="rounded-2xl border border-[#3b82f6]/10 bg-[#020617] px-5 py-5 shadow-[0_20px_60px_rgba(2,6,23,0.12)]"
                  >
                    <p className="text-sm font-bold text-slate-100">{title}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-400">{copy}</p>
                  </article>
                ))}
              </div>
              <div className="grid gap-6 lg:grid-cols-3">
                {pricingPlans.map((plan) => {
                  const meta = getPlanMeta(plan.key);

                  return (
                  <article
                    key={plan.key}
                    className={`rounded-2xl border p-8 ${
                      plan.featured
                        ? "border-[#3b82f6]/40 bg-[linear-gradient(180deg,rgba(30,64,175,0.22),rgba(15,23,42,0.98))] shadow-[0_24px_70px_rgba(59,130,246,0.16)]"
                        : "border-[#3b82f6]/10 bg-[#020617]"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-xs font-bold uppercase tracking-[0.24em] text-[#60a5fa]">{meta.label}</p>
                        <div className="mt-4 flex items-end gap-1">
                          <span className="text-4xl font-black tracking-tight text-slate-100">{meta.price}</span>
                          {meta.cadence ? <span className="pb-1 text-sm text-slate-400">{meta.cadence}</span> : null}
                        </div>
                      </div>
                      {plan.featured ? (
                        <span className="rounded-full border border-[#60a5fa]/30 bg-[#3b82f6]/10 px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] text-[#93c5fd]">
                          Most popular
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-5 text-sm leading-7 text-slate-400">{meta.summary}</p>
                    <div className="mt-6 rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-4">
                      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Usage</p>
                      <p className="mt-2 text-lg font-semibold text-slate-100">{meta.dailyLimitLabel}</p>
                    </div>
                    <ul className="mt-6 space-y-3">
                      {plan.features.map((feature) => (
                        <li key={feature} className="flex items-start gap-3 text-sm text-slate-300">
                          <AppIcon className="mt-0.5 h-5 w-5 shrink-0 text-[#3b82f6]" name="check" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <a
                      className={`mt-8 inline-flex w-full items-center justify-center rounded-xl px-5 py-3 text-sm font-bold transition ${
                        plan.featured
                          ? "bg-[#3b82f6] text-white hover:brightness-110"
                          : "border border-[#3b82f6]/20 bg-[#3b82f6]/10 text-[#93c5fd] hover:bg-[#3b82f6]/20"
                      }`}
                      href={plan.ctaHref}
                      rel={plan.ctaHref.startsWith("http") ? "noreferrer" : undefined}
                      target={plan.ctaHref.startsWith("http") ? "_blank" : undefined}
                    >
                      {plan.ctaLabel}
                    </a>
                  </article>
                  );
                })}
              </div>
            </div>
          </section>

          <section className="py-24" id="developers">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="grid items-center gap-16 lg:grid-cols-2">
                <div className="space-y-6">
                  <h2 className="text-4xl font-bold tracking-tight text-slate-100">Deployer and Wallet Intelligence</h2>
                  <p className="text-lg text-slate-400">
                    Surface the wallet-level signals traders usually have to stitch together by hand: shared funders, linked holder clusters, seller pressure, and repeat launch behaviour.
                  </p>
                  <ul className="space-y-4">
                    {developerBullets.map((bullet) => (
                      <li key={bullet} className="flex items-center gap-3">
                        <AppIcon className="h-5 w-5 text-[#3b82f6]" name="check" />
                        <span>{bullet}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="flex flex-wrap gap-3">
                    <Link className="inline-flex rounded-lg border border-[#3b82f6]/30 bg-[#3b82f6]/10 px-6 py-3 font-bold text-[#3b82f6]" href="/developers">
                      Open developer intel
                    </Link>
                    <span className="inline-flex rounded-lg border border-white/10 bg-white/5 px-6 py-3 font-bold text-slate-300">
                      Live in token reports
                    </span>
                  </div>
                </div>
                <div className="group relative">
                  <div className="absolute -inset-1 rounded-xl bg-[#3b82f6]/20 opacity-30 blur transition duration-1000 group-hover:opacity-50" />
                  <div className="relative overflow-hidden rounded-xl border border-white/10 bg-[#0a1120] p-6">
                    <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
                      <div>
                        <p className="text-xs font-bold uppercase tracking-[0.22em] text-slate-500">Signal layer</p>
                        <p className="mt-1 text-sm font-semibold text-slate-200">What traders do not want to trace by hand</p>
                      </div>
                      <span className="rounded-full border border-[#3b82f6]/30 bg-[#3b82f6]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#93c5fd]">
                        Live
                      </span>
                    </div>
                    <div className="grid gap-3">
                      {developerIntelPreview.map((item) => (
                        <article key={item.label} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                          <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-slate-500">{item.label}</p>
                          <p className="mt-3 text-lg font-semibold text-slate-100">{item.value}</p>
                          <p className="mt-2 text-sm leading-6 text-slate-400">{item.detail}</p>
                        </article>
                      ))}
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
                  <li>Developer Intel</li>
                  <li>Live Feed</li>
                  <li>Pricing</li>
                  <li>Team</li>
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
