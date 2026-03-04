import Link from "next/link";
import { getCheckById } from "@/lib/api";
import { statusTone } from "@/lib/mock-data";

type ReportPageProps = {
  params: Promise<{
    entityType: string;
    reportId: string;
  }>;
};

export default async function ReportPage({ params }: ReportPageProps) {
  const { reportId } = await params;
  const report = await getCheckById(reportId);

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <div className="mx-auto w-full max-w-[1240px] px-5 py-6 md:px-8 md:py-8">
        <header className="mb-7 flex flex-col gap-5 rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] px-5 py-5 shadow-[0_18px_60px_rgba(20,34,27,0.08)] backdrop-blur md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
              RESULT PAGE
            </p>
            <h1 className="mt-2 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em] md:text-5xl">
              Explainable risk report
            </h1>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              className="rounded-full border border-[color:var(--border)] bg-white/70 px-5 py-3 text-center text-sm font-bold"
              href="/dashboard"
            >
              К dashboard
            </Link>
            <button className="rounded-full bg-[linear-gradient(135deg,#b43f28,#db6b4f)] px-5 py-3 text-sm font-bold text-white">
              Recheck
            </button>
          </div>
        </header>

        <section className="grid gap-6 md:grid-cols-[0.9fr_1.1fr]">
          <aside className="rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] p-6">
            <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
              SUMMARY
            </p>
            <h2 className="mt-3 text-2xl font-bold">{report.displayName}</h2>
            <p className="mt-4 text-sm leading-7 text-[var(--muted)]">{report.summary}</p>

            <div className="mt-5 flex flex-wrap gap-2">
              <span
                className={`rounded-full px-4 py-2 text-xs font-extrabold uppercase tracking-[0.14em] ${statusTone[report.status]}`}
              >
                {report.status}
              </span>
              <span className="rounded-full bg-[rgba(13,122,95,0.08)] px-4 py-2 text-xs font-bold text-[var(--accent-deep)]">
                Confidence {report.confidence}
              </span>
            </div>

            <div className="mt-6 grid gap-3">
              {[
                ["Entity", report.entityId],
                ["Updated", report.refreshedAt],
                ["Review queue", report.reviewState],
                ["Liquidity", report.liquidity],
              ].map(([label, value]) => (
                <article key={label} className="rounded-3xl bg-white/80 px-4 py-4">
                  <span className="text-sm text-[var(--muted)]">{label}</span>
                  <strong className="mt-2 block break-all text-base">{value}</strong>
                </article>
              ))}
            </div>
          </aside>

          <div className="rounded-[32px] border border-[color:var(--border)] bg-white/82 p-6">
            <div className="flex flex-col gap-5 md:flex-row md:items-center">
              <div className="grid h-32 w-32 place-items-center rounded-full bg-[radial-gradient(circle_closest-side,#fff_67%,transparent_68%_100%),conic-gradient(#c84b31_0_82%,rgba(200,75,49,0.14)_82%_100%)]">
                <span className="font-[family:var(--font-display)] text-5xl font-bold">
                  {report.score}
                </span>
              </div>
              <div className="flex-1">
                <p className="text-sm text-[var(--muted)]">Итоговый risk score</p>
                <strong className="mt-2 block text-lg leading-8">
                  {report.summary}
                </strong>
                <span className="mt-2 block text-sm text-[var(--muted)]">
                  Background refresh: {report.timeline[report.timeline.length - 1]?.value}
                </span>
              </div>
            </div>

            <div className="mt-7 grid gap-3 md:grid-cols-4">
              {report.metrics.map((metric) => (
                <article key={metric.label} className="rounded-3xl bg-[rgba(244,241,232,0.72)] px-4 py-4">
                  <span className="text-sm text-[var(--muted)]">{metric.label}</span>
                  <strong className="mt-2 block text-lg">{metric.value}</strong>
                </article>
              ))}
            </div>

            <section className="mt-7">
              <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
                TOP FINDINGS
              </p>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                {report.factors.map((factor) => (
                  <article
                    key={factor.code}
                    className="rounded-[28px] border border-[color:var(--border)] bg-[rgba(244,241,232,0.72)] p-4"
                  >
                    <span className="text-[11px] font-extrabold tracking-[0.16em] text-[var(--critical)]">
                      {factor.severity}
                    </span>
                    <strong className="mt-2 block leading-6">{factor.label}</strong>
                    <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                      {factor.explanation}
                    </p>
                    <span className="mt-3 block text-sm font-bold text-[var(--accent-deep)]">
                      Weight {factor.weight}
                    </span>
                  </article>
                ))}
              </div>
            </section>

            <section className="mt-7">
              <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
                TIMELINE
              </p>
              <div className="mt-4 grid gap-3">
                {report.timeline.map((event) => (
                  <div
                    key={event.label}
                    className="flex flex-col gap-2 rounded-3xl bg-[rgba(244,241,232,0.72)] px-4 py-4 md:flex-row md:items-center md:justify-between"
                  >
                    <span className="text-sm text-[var(--muted)]">{event.label}</span>
                    <strong
                      className={
                        event.tone === "danger"
                          ? "text-[var(--critical)]"
                          : event.tone === "warn"
                            ? "text-[#99660e]"
                            : "text-[var(--foreground)]"
                      }
                    >
                      {event.value}
                    </strong>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </section>
      </div>
    </main>
  );
}
