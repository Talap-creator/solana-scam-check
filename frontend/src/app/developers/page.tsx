import Link from "next/link";
import { DeveloperWalletBoard } from "@/components/developer-wallet-board";
import { AppIcon } from "@/components/app-icon";
import { LandingHeaderAction } from "@/components/landing-header-action";
import { getDeveloperProfiles } from "@/lib/api";

const landingNav = [
  { href: "/#engine", label: "Intelligence" },
  { href: "/coins", label: "Live Feed" },
  { href: "/developers", label: "Developers" },
  { href: "/#team", label: "Team" },
  { href: "/#pricing", label: "Pricing" },
] as const;

export default async function DevelopersPage() {
  const profiles = await getDeveloperProfiles();

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

        <section className="pb-20 pt-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <DeveloperWalletBoard profiles={profiles} />
          </div>
        </section>
      </div>
    </main>
  );
}
