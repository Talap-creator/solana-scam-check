import Link from "next/link";
import { AppIcon } from "@/components/app-icon";
import { LandingHeaderAction } from "@/components/landing-header-action";
import { SearchCheckForm } from "@/components/search-check-form";
import { APP_TELEGRAM_URL } from "@/lib/plans";

const signalCards = [
  {
    copy: "We surface holder wallets funded from the same route, even when the overlap is multi-hop and not obvious from a single explorer view.",
    icon: "hub" as const,
    title: "Shared funder graph",
  },
  {
    copy: "See how much tracked supply is controlled by the linked developer cluster instead of trying to estimate concentration wallet by wallet.",
    icon: "groups" as const,
    title: "Cluster supply control",
  },
  {
    copy: "We highlight when exits compress into the same sell window, which is much harder to notice by manually watching transfers.",
    icon: "chart" as const,
    title: "Exit timing compression",
  },
  {
    copy: "Spot direct wallet overlap, shared outgoing routes, and recycled launch behaviour before it is obvious in price action.",
    icon: "history" as const,
    title: "Launch recycling",
  },
] as const;

const operatorCards = [
  {
    detail: "Before buying, check whether the dev cluster is funding its own holder base, how much supply it controls, and whether exits are already coordinated.",
    title: "Token report",
  },
  {
    detail: "Before copy-trading, check whether the wallet has a launch-dump pattern, risky counterparties, or repeat-deployer fingerprints.",
    title: "Wallet checker",
  },
  {
    detail: "Before chasing a launch, filter for organic vs insider-style patterns and move the obvious cluster-driven launches out of your queue.",
    title: "Launch feed",
  },
] as const;

const proofItems = [
  {
    label: "Shared funding coverage",
    value: "42.0%",
    copy: "Share of tracked holder wallets that still map back into the same funding graph.",
  },
  {
    label: "Cluster supply control",
    value: "18.4%",
    copy: "Tracked supply estimated to sit inside the linked holder cluster.",
  },
  {
    label: "Exit wallet density",
    value: "2 wallets",
    copy: "Large-holder wallets already contributing to coordinated exit pressure.",
  },
  {
    label: "Funding trace depth",
    value: "1.7 hops",
    copy: "Average graph depth before the funding trace breaks.",
  },
  {
    label: "Direct transfer overlap",
    value: "1 route",
    copy: "Tracked holder wallets transferring directly between each other.",
  },
  {
    label: "Activity timing similarity",
    value: "61.0%",
    copy: "How tightly wallet activity is clustered instead of looking organic.",
  },
] as const;

const landingNav = [
  { href: "/#engine", label: "Intelligence" },
  { href: "/coins", label: "Live Feed" },
  { href: "/developers", label: "Developers" },
  { href: "/#team", label: "Team" },
  { href: "/#pricing", label: "Pricing" },
] as const;

export default function DevelopersPage() {
  return (
    <main className="min-h-screen bg-[#020617] text-slate-100 antialiased">
      <div className="relative flex min-h-screen flex-col overflow-x-hidden">
        <header className="sticky top-0 z-50 w-full border-b border-[rgba(59,130,246,0.1)] bg-[rgba(2,6,23,0.82)] backdrop-blur-md">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex min-h-16 flex-wrap items-center justify-between gap-3 py-3 md:h-16 md:flex-nowrap md:py-0">
              <div className="flex items-center gap-8">
                <Link className="flex items-center gap-2 text-[#3b82f6]" href="/">
                  <AppIcon className="h-8 w-8" name="shield" />
                  <h2 className="text-xl font-bold tracking-tight text-slate-100">SolanaTrust</h2>
                </Link>
                <nav className="hidden items-center gap-6 md:flex">
                  {landingNav.map((item) => (
                    <Link
                      key={item.href}
                      className={`text-sm font-medium transition-colors hover:text-[#3b82f6] ${
                        item.href === "/developers" ? "text-white" : "text-slate-300"
                      }`}
                      href={item.href}
                    >
                      {item.label}
                    </Link>
                  ))}
                </nav>
              </div>
              <div className="flex items-center gap-4">
                <LandingHeaderAction />
              </div>
              <nav className="-mx-1 flex w-full gap-2 overflow-x-auto px-1 pb-1 md:hidden">
                {landingNav.map((item) => (
                  <Link
                    key={item.href}
                    className={`shrink-0 rounded-full px-3 py-2 text-xs font-bold uppercase tracking-[0.14em] ${
                      item.href === "/developers"
                        ? "border border-[#3b82f6]/30 bg-[#3b82f6]/15 text-[#93c5fd]"
                        : "border border-[#3b82f6]/20 bg-[#3b82f6]/10 text-[#93c5fd]"
                    }`}
                    href={item.href}
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
            </div>
          </div>
        </header>

        <section className="relative overflow-hidden py-16 sm:py-20 lg:py-28">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.12),transparent_30%)]" />
          <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid items-center gap-12 lg:grid-cols-[minmax(0,1fr)_420px]">
              <div className="space-y-8">
                <div className="space-y-4">
                  <span className="inline-flex items-center rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] text-[#93c5fd]">
                    Developer And Wallet Intelligence
                  </span>
                  <h1 className="max-w-4xl text-4xl font-black tracking-[-0.05em] text-white sm:text-5xl lg:text-6xl">
                    See the wallets behind the launch, not just the token chart.
                  </h1>
                  <p className="max-w-3xl text-lg leading-8 text-slate-400">
                    SolanaTrust pulls forward the wallet-level context traders usually spend too much time collecting:
                    shared funders, linked holder clusters, repeat deployer behaviour, and coordinated exits.
                  </p>
                </div>
                <div className="max-w-3xl">
                  <SearchCheckForm
                    leadingIcon
                    placeholder="Paste a token mint, wallet, or project URL"
                    submitLabel="Open analysis"
                    variant="landing"
                  />
                </div>
                <div className="flex flex-wrap gap-3">
                  <Link className="rounded-lg border border-[#3b82f6]/30 bg-[#3b82f6]/10 px-5 py-3 text-sm font-bold text-[#93c5fd]" href="/coins">
                    Open launch feed
                  </Link>
                  <a
                    className="rounded-lg border border-white/10 bg-white/5 px-5 py-3 text-sm font-bold text-slate-100"
                    href={APP_TELEGRAM_URL}
                    rel="noreferrer"
                    target="_blank"
                  >
                    Request premium access
                  </a>
                </div>
              </div>

              <div className="rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(8,17,32,0.98),rgba(6,14,26,0.98))] p-6 shadow-[0_24px_80px_rgba(2,6,23,0.45)]">
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-slate-500">What we surface</p>
                    <p className="mt-1 text-sm text-slate-300">Signals that usually take multiple explorer passes to confirm.</p>
                  </div>
                  <span className="rounded-full border border-[#3b82f6]/25 bg-[#3b82f6]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#93c5fd]">
                    Live
                  </span>
                </div>
                <div className="mt-4 grid gap-3">
                  {proofItems.map((item) => (
                    <article key={item.label} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                      <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">{item.label}</p>
                      <p className="mt-3 text-lg font-semibold text-white">{item.value}</p>
                      <p className="mt-2 text-sm leading-6 text-slate-400">{item.copy}</p>
                    </article>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="py-6 sm:py-10">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {signalCards.map((item) => (
                <article key={item.title} className="rounded-[24px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-5">
                  <div className="rounded-2xl border border-[#3b82f6]/20 bg-[#3b82f6]/10 p-3 text-[#93c5fd]">
                    <AppIcon className="h-5 w-5" name={item.icon} />
                  </div>
                  <h2 className="mt-5 text-xl font-bold text-white">{item.title}</h2>
                  <p className="mt-3 text-sm leading-7 text-slate-400">{item.copy}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="py-16">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mb-10 max-w-3xl">
              <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Where traders actually use this</h2>
              <p className="mt-4 text-lg text-slate-400">
                The value is not another generic score. It is faster operator context at the moment you need to decide.
              </p>
            </div>
            <div className="grid gap-4 lg:grid-cols-3">
              {operatorCards.map((item) => (
                <article key={item.title} className="rounded-[24px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(8,14,26,0.98))] p-6">
                  <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[#93c5fd]">{item.title}</p>
                  <p className="mt-4 text-sm leading-7 text-slate-300">{item.detail}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="pb-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="rounded-[32px] border border-[#3b82f6]/20 bg-[linear-gradient(180deg,rgba(9,19,35,0.96),rgba(7,16,29,0.98))] p-8 shadow-[0_24px_80px_rgba(2,6,23,0.45)]">
              <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_240px] lg:items-center">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.26em] text-[#93c5fd]">Premium operator layer</p>
                  <h2 className="mt-3 text-3xl font-bold tracking-tight text-white">Deployer and wallet context is what traders actually pay for.</h2>
                  <p className="mt-4 max-w-3xl text-base leading-8 text-slate-400">
                    Traders will pay for signals that are faster and harder to reconstruct: shared funders, linked exits,
                    wallet reputation, launch recycling, and deployer history. That is the layer we are building out.
                  </p>
                </div>
                <div className="flex flex-col gap-3">
                  <Link className="rounded-xl bg-[#3b82f6] px-5 py-3 text-center text-sm font-bold text-white" href="/register">
                    Create account
                  </Link>
                  <a
                    className="rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-center text-sm font-bold text-slate-100"
                    href={APP_TELEGRAM_URL}
                    rel="noreferrer"
                    target="_blank"
                  >
                    Talk on Telegram
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
