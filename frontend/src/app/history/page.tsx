import Link from "next/link";
import { getChecks } from "@/lib/api";
import { statusTone } from "@/lib/mock-data";

export default async function HistoryPage() {
  const checks = await getChecks();

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <div className="mx-auto w-full max-w-[1240px] px-5 py-6 md:px-8 md:py-8">
        <header className="mb-7 flex flex-col gap-5 rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] px-5 py-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
              HISTORY
            </p>
            <h1 className="mt-2 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em] md:text-5xl">
              Последние проверки
            </h1>
          </div>
          <Link className="rounded-full bg-[linear-gradient(135deg,#0f5a48,#0d7a5f)] px-5 py-3 text-center text-sm font-bold text-white" href="/dashboard">
            Назад в dashboard
          </Link>
        </header>

        <section className="rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] p-6">
          <div className="grid gap-4">
            {checks.map((report) => (
              <Link
                key={report.id}
                href={`/report/${report.entityType}/${report.id}`}
                className="grid gap-3 rounded-[28px] border border-[color:var(--border)] bg-white/80 p-5 md:grid-cols-[1.4fr_0.7fr_0.7fr_0.8fr]"
              >
                <div>
                  <strong className="text-lg">{report.displayName}</strong>
                  <p className="mt-2 text-sm leading-7 text-[var(--muted)]">{report.summary}</p>
                </div>
                <div>
                  <span className="text-sm text-[var(--muted)]">Score</span>
                  <strong className="mt-1 block text-2xl">{report.score}</strong>
                </div>
                <div>
                  <span className="text-sm text-[var(--muted)]">Updated</span>
                  <strong className="mt-1 block">{report.refreshedAt}</strong>
                </div>
                <div className="flex items-start md:justify-end">
                  <span className={`rounded-full px-3 py-1 text-xs font-extrabold uppercase tracking-[0.14em] ${statusTone[report.status]}`}>
                    {report.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
