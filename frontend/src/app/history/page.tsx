import Link from "next/link";
import { PlatformShell } from "@/components/platform-shell";
import { getChecks } from "@/lib/api";
import { statusTone } from "@/lib/mock-data";

export default async function HistoryPage() {
  const checks = await getChecks();

  return (
    <PlatformShell
      actions={[
        { href: "/dashboard", label: "Dashboard", tone: "secondary" },
        { href: "/coins", label: "Open launch feed" },
      ]}
      eyebrow="History"
      stats={[
        { label: "Stored checks", value: String(checks.length) },
        { label: "High risk", value: String(checks.filter((item) => item.status === "high" || item.status === "critical").length) },
        { label: "Low risk", value: String(checks.filter((item) => item.status === "low").length) },
        { label: "Latest item", value: checks[0]?.refreshedAt ?? "n/a" },
      ]}
      subtitle="Historical scan ledger for reports that have already moved through the engine."
      title="Historical scan ledger"
    >
      <section className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-6">
        <div className="grid gap-4">
          {checks.map((report) => (
            <Link
              key={report.id}
              className="grid gap-3 rounded-[20px] border border-[rgba(59,130,246,0.14)] bg-[rgba(59,130,246,0.05)] p-5 transition-colors hover:bg-[rgba(59,130,246,0.08)] md:grid-cols-[1.4fr_0.7fr_0.7fr_0.8fr]"
              href={`/report/${report.entityType}/${report.id}`}
            >
              <div>
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-xl border border-[rgba(59,130,246,0.16)] bg-[rgba(59,130,246,0.12)] font-[family:var(--font-display)] text-sm text-[#60a5fa]">
                    {report.displayName.slice(0, 1)}
                  </div>
                  <div>
                    <strong className="text-lg text-slate-100">{report.displayName}</strong>
                    {(report.name || report.symbol) ? (
                      <p className="text-sm text-slate-400">
                        {[report.symbol, report.name].filter(Boolean).join(" | ")}
                      </p>
                    ) : null}
                  </div>
                </div>
                <p className="mt-2 text-sm leading-7 text-slate-400">{report.summary}</p>
              </div>
              <div>
                <span className="text-sm text-slate-500">Score</span>
                <strong className="mt-1 block text-2xl text-slate-100">{report.score}</strong>
              </div>
              <div>
                <span className="text-sm text-slate-500">Updated</span>
                <strong className="mt-1 block text-slate-100">{report.refreshedAt}</strong>
              </div>
              <div className="flex items-start md:justify-end">
                <span
                  className={`rounded-full px-3 py-1 text-xs font-extrabold uppercase tracking-[0.14em] ${statusTone[report.status]}`}
                >
                  {report.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </PlatformShell>
  );
}
