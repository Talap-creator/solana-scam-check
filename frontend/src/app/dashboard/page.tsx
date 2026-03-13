import Link from "next/link";
import { DashboardHeaderActions } from "@/components/dashboard-header-actions";
import { PlatformShell } from "@/components/platform-shell";
import { getChecks, getOverview, getWatchlist } from "@/lib/api";
import { statusTone } from "@/lib/mock-data";

function severityClass(value: string) {
  if (/critical|high/i.test(value)) return "text-rose-400";
  if (/medium|watch|review/i.test(value)) return "text-amber-400";
  return "text-emerald-400";
}

export default async function DashboardPage() {
  const [overview, checks, watchlist] = await Promise.all([getOverview(), getChecks(), getWatchlist()]);
  const recentReports = checks.slice(0, 4);
  const queueReports = checks.filter((item) => item.status === "high" || item.status === "critical").slice(0, 3);
  const activeWatchlist = watchlist.slice(0, 4);

  return (
    <PlatformShell
      eyebrow="Dashboard"
      headerContent={<DashboardHeaderActions />}
      stats={[
        { label: "Total checks", value: String(overview.totals.checks) },
        { label: "Watchlist", value: String(overview.totals.watchlist) },
        { label: "Review queue", value: String(overview.totals.review_queue) },
        { label: "Active rules", value: String(overview.active_rules) },
      ]}
      subtitle="Operational overview of recent reports, tracked entities, and actions that need attention across the SolanaTrust engine."
      title="Risk intelligence dashboard"
    >
      <section className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <article className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">Recent reports</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-slate-100">Latest completed scans</h2>
            </div>
            <p className="text-sm text-slate-400">Freshest reports currently available in your workspace.</p>
          </div>

          <div className="mt-5 grid gap-4">
            {recentReports.map((report) => (
              <Link
                key={report.id}
                className="grid gap-3 rounded-[20px] border border-[rgba(59,130,246,0.14)] bg-[rgba(59,130,246,0.05)] p-5 transition-colors hover:bg-[rgba(59,130,246,0.08)] md:grid-cols-[1.2fr_0.5fr_0.7fr_0.6fr]"
                href={`/report/${report.entityType}/${report.id}`}
              >
                <div>
                  <div className="flex items-center gap-3">
                    <div className="grid h-10 w-10 place-items-center rounded-xl border border-[rgba(59,130,246,0.18)] bg-[rgba(59,130,246,0.12)] font-[family:var(--font-display)] text-sm font-bold text-[#60a5fa]">
                      {report.displayName.slice(0, 1)}
                    </div>
                    <div>
                      <strong className="text-lg text-slate-100">{report.displayName}</strong>
                      <p className="text-sm text-slate-400">
                        {[report.symbol, report.name].filter(Boolean).join(" | ") || report.entityType}
                      </p>
                    </div>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-400">{report.summary}</p>
                </div>
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Score</p>
                  <strong className="mt-2 block text-3xl text-slate-100">{report.score}</strong>
                </div>
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Liquidity</p>
                  <strong className="mt-2 block text-slate-100">{report.liquidity}</strong>
                  <p className="mt-3 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Updated</p>
                  <span className="mt-2 block text-sm text-slate-400">{report.refreshedAt}</span>
                </div>
                <div className="flex items-start md:justify-end">
                  <span className={`rounded-full px-3 py-1 text-xs font-extrabold uppercase tracking-[0.14em] ${statusTone[report.status]}`}>
                    {report.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </article>

        <div className="grid gap-6">
          <article className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-6">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">System state</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-slate-100">Engine status</h2>
            <div className="mt-5 grid gap-3">
              <div className="rounded-[18px] border border-[rgba(59,130,246,0.14)] bg-[rgba(59,130,246,0.06)] p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Freshness</p>
                <strong className="mt-2 block text-lg text-slate-100">{overview.freshness}</strong>
              </div>
              <div className="rounded-[18px] border border-[rgba(59,130,246,0.14)] bg-[rgba(59,130,246,0.06)] p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Network</p>
                <strong className="mt-2 block text-lg uppercase text-slate-100">{overview.network}</strong>
              </div>
              <div className="rounded-[18px] border border-[rgba(59,130,246,0.14)] bg-[rgba(59,130,246,0.06)] p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Supported entities</p>
                <strong className="mt-2 block text-lg text-slate-100">{overview.supported_entities.join(", ")}</strong>
              </div>
            </div>
          </article>

          <article className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-6">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">Quick actions</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-slate-100">Move through the platform</h2>
            <div className="mt-5 grid gap-3">
              <Link className="rounded-[18px] border border-[rgba(59,130,246,0.16)] bg-[rgba(59,130,246,0.08)] px-4 py-4 text-sm font-semibold text-slate-100 transition-colors hover:bg-[rgba(59,130,246,0.14)]" href="/coins">
                Review the live launch feed
              </Link>
              <Link className="rounded-[18px] border border-[rgba(59,130,246,0.16)] bg-[rgba(59,130,246,0.08)] px-4 py-4 text-sm font-semibold text-slate-100 transition-colors hover:bg-[rgba(59,130,246,0.14)]" href="/watchlist">
                Open tracked entities
              </Link>
              <Link className="rounded-[18px] border border-[rgba(59,130,246,0.16)] bg-[rgba(59,130,246,0.08)] px-4 py-4 text-sm font-semibold text-slate-100 transition-colors hover:bg-[rgba(59,130,246,0.14)]" href="/history">
                Browse historical scans
              </Link>
            </div>
          </article>
        </div>
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <article className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-6">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">Watchlist pulse</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-slate-100">Tracked entities</h2>
            </div>
            <Link className="text-sm font-semibold text-[#60a5fa]" href="/watchlist">
              Open watchlist
            </Link>
          </div>

          <div className="mt-5 grid gap-3">
            {activeWatchlist.map((item) => (
              <article key={`${item.name}-${item.delta}`} className="rounded-[18px] border border-[rgba(59,130,246,0.14)] bg-[rgba(59,130,246,0.06)] p-4">
                <div className="flex items-start justify-between gap-3">
                  <strong className="text-lg text-slate-100">{item.name}</strong>
                  <span className={`text-xs font-bold uppercase tracking-[0.14em] ${severityClass(item.state)}`}>{item.state}</span>
                </div>
                <p className="mt-3 text-sm text-slate-400">{item.delta}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-6">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">Review queue</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-slate-100">Items that need attention</h2>
            </div>
            <span className="rounded-full border border-[rgba(59,130,246,0.18)] bg-[rgba(59,130,246,0.08)] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-[#60a5fa]">
              {queueReports.length} active
            </span>
          </div>

          <div className="mt-5 overflow-hidden rounded-[20px] border border-[rgba(59,130,246,0.14)]">
            <div className="hidden grid-cols-[minmax(0,1.1fr)_120px_150px] bg-[rgba(59,130,246,0.08)] px-4 py-3 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500 md:grid">
              <span>Asset</span>
              <span>Score</span>
              <span>Status</span>
            </div>
            {queueReports.map((report) => (
              <Link
                key={`queue-${report.id}`}
                className="flex flex-col gap-3 border-t border-[rgba(59,130,246,0.10)] px-4 py-4 transition-colors hover:bg-[rgba(59,130,246,0.06)] md:grid md:grid-cols-[minmax(0,1.1fr)_120px_150px] md:items-center"
                href={`/report/${report.entityType}/${report.id}`}
              >
                <div className="min-w-0">
                  <strong className="block truncate text-slate-100">{report.displayName}</strong>
                  <span className="text-sm text-slate-400">{report.entityType}</span>
                </div>
                <div className="flex flex-wrap items-center gap-3 md:contents">
                  <strong className="text-slate-100 md:block">{report.score}</strong>
                  <span className={`w-fit rounded-full px-3 py-1 text-xs font-extrabold uppercase tracking-[0.14em] ${statusTone[report.status]}`}>
                    {report.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </article>
      </section>
    </PlatformShell>
  );
}
