import Link from "next/link";
import { getChecks, getWatchlist } from "@/lib/api";
import { statusTone } from "@/lib/mock-data";

export default async function DashboardPage() {
  const [checks, watchlist] = await Promise.all([getChecks(), getWatchlist()]);

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <div className="mx-auto w-full max-w-[1240px] px-5 py-6 md:px-8 md:py-8">
        <header className="mb-7 flex flex-col gap-5 rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] px-5 py-5 shadow-[0_18px_60px_rgba(20,34,27,0.08)] backdrop-blur md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
              DASHBOARD
            </p>
            <h1 className="mt-2 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em] md:text-5xl">
              Быстрые проверки и очередь риска
            </h1>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              className="rounded-full border border-[color:var(--border)] bg-white/70 px-5 py-3 text-center text-sm font-bold"
              href="/"
            >
              На главную
            </Link>
            <Link
              className="rounded-full bg-[linear-gradient(135deg,#0f5a48,#0d7a5f)] px-5 py-3 text-center text-sm font-bold text-white shadow-[0_18px_36px_rgba(13,122,95,0.22)]"
              href="/report/token/pearl-token"
            >
              Открыть demo report
            </Link>
          </div>
        </header>

        <section className="grid gap-6 md:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] p-6">
            <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
              UNIVERSAL CHECK
            </p>
            <h2 className="mt-3 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em]">
              Один инпут для token, wallet и project
            </h2>
            <div className="mt-6 flex flex-col gap-3 rounded-[28px] border border-[color:var(--border)] bg-white/85 p-3 md:flex-row">
              <input
                defaultValue="9xQeWvG816bUx9EPfEZLQ7ZL8A6V7zVYhWf9e7s6PzF1"
                className="min-w-0 flex-1 rounded-2xl border border-transparent bg-transparent px-4 py-4 text-sm outline-none"
                placeholder="Вставь address или URL проекта"
                type="text"
              />
              <button className="rounded-3xl bg-[linear-gradient(135deg,#b43f28,#db6b4f)] px-6 py-4 text-sm font-extrabold text-white">
                Check now
              </button>
            </div>
            <div className="mt-6 grid gap-3 md:grid-cols-3">
              {[
                ["Risk rules", "128 active"],
                ["Review queue", "14 entities"],
                ["Freshness", "< 15 min"],
              ].map(([label, value]) => (
                <article key={label} className="rounded-3xl bg-white/80 px-4 py-4">
                  <span className="text-sm text-[var(--muted)]">{label}</span>
                  <strong className="mt-2 block text-lg">{value}</strong>
                </article>
              ))}
            </div>
          </div>

          <aside className="rounded-[32px] border border-[color:var(--border)] bg-[linear-gradient(135deg,rgba(13,122,95,0.06),rgba(255,255,255,0.72))] p-6">
            <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
              WATCHLIST
            </p>
            <h2 className="mt-3 text-2xl font-bold">Что изменилось с прошлого check</h2>
            <div className="mt-5 grid gap-3">
              {watchlist.map((item) => (
                <article
                  key={item.name}
                  className="rounded-3xl border border-[color:var(--border)] bg-white/80 px-4 py-4"
                >
                  <strong className="block">{item.name}</strong>
                  <div className="mt-2 flex items-center justify-between gap-3 text-sm text-[var(--muted)]">
                    <span>{item.delta}</span>
                    <span>{item.state}</span>
                  </div>
                </article>
              ))}
            </div>
          </aside>
        </section>

        <section className="mt-7 rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] p-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
                RECENT CHECKS
              </p>
              <h2 className="mt-3 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em]">
                История и active review queue
              </h2>
            </div>
            <div className="flex flex-wrap gap-2 text-sm">
              {["All", "Token", "Wallet", "Project", "High+", "Needs review"].map((item) => (
                <span
                  key={item}
                  className="rounded-full border border-[color:var(--border)] bg-white/80 px-4 py-2"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-6 grid gap-4">
            {checks.map((report) => (
              <article
                key={report.id}
                className="grid gap-4 rounded-[28px] border border-[color:var(--border)] bg-white/80 p-5 md:grid-cols-[1.3fr_0.8fr_0.8fr_auto] md:items-center"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <strong className="text-lg">{report.displayName}</strong>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-extrabold uppercase tracking-[0.14em] ${statusTone[report.status]}`}
                    >
                      {report.status}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-7 text-[var(--muted)]">
                    {report.summary}
                  </p>
                </div>
                <div className="text-sm text-[var(--muted)]">
                  <span className="block">Score</span>
                  <strong className="mt-1 block text-2xl text-[var(--foreground)]">
                    {report.score}
                  </strong>
                </div>
                <div className="text-sm text-[var(--muted)]">
                  <span className="block">Updated</span>
                  <strong className="mt-1 block text-base text-[var(--foreground)]">
                    {report.refreshedAt}
                  </strong>
                </div>
                <Link
                  className="rounded-full bg-[linear-gradient(135deg,#0f5a48,#0d7a5f)] px-5 py-3 text-center text-sm font-bold text-white"
                  href={`/report/${report.entityType}/${report.id}`}
                >
                  Open report
                </Link>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
