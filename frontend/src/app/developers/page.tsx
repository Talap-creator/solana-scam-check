import Link from "next/link";
import { DeveloperWalletBoard } from "@/components/developer-wallet-board";
import { AppIcon } from "@/components/app-icon";
import { LandingHeaderAction } from "@/components/landing-header-action";
import { SearchCheckForm } from "@/components/search-check-form";
import { getChecks } from "@/lib/api";
import { deriveDeveloperLeadProfiles } from "@/lib/developer-leads";

const landingNav = [
  { href: "/#engine", label: "Intelligence" },
  { href: "/coins", label: "Live Feed" },
  { href: "/developers", label: "Developers" },
  { href: "/#team", label: "Team" },
  { href: "/#pricing", label: "Pricing" },
] as const;

const valueProps = [
  "Which launch wallets repeatedly show up around risky launches",
  "Which linked holder clusters control more supply than they should",
  "Which launches already show compressed exit behaviour",
] as const;

export default async function DevelopersPage() {
  const checks = await getChecks();
  const profiles = deriveDeveloperLeadProfiles(checks);

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

        <section className="relative overflow-hidden py-16 sm:py-20">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.12),transparent_28%)]" />
          <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="space-y-8">
              <div className="space-y-4">
                <span className="inline-flex items-center rounded-full border border-[#3b82f6]/20 bg-[#3b82f6]/10 px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] text-[#93c5fd]">
                  Launch Wallet Intelligence
                </span>
                <h1 className="max-w-5xl text-4xl font-black tracking-[-0.05em] text-white sm:text-5xl lg:text-6xl">
                  Wallets launching tokens, ranked like a feed.
                </h1>
                <p className="max-w-4xl text-lg leading-8 text-slate-400">
                  This page is the wallet side of the launch feed: repeat launch wallets, hidden clusters, linked funding,
                  and risky operators surfaced in one board instead of making you trace them manually one by one.
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
              <div className="grid gap-3 md:grid-cols-3">
                {valueProps.map((item) => (
                  <div key={item} className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-4 text-sm leading-6 text-slate-300">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="pb-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <DeveloperWalletBoard profiles={profiles} />
          </div>
        </section>
      </div>
    </main>
  );
}
