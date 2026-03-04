import Link from "next/link";
import { getWatchlist } from "@/lib/api";

export default async function WatchlistPage() {
  const items = await getWatchlist();

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <div className="mx-auto w-full max-w-[1240px] px-5 py-6 md:px-8 md:py-8">
        <header className="mb-7 flex flex-col gap-5 rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] px-5 py-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
              WATCHLIST
            </p>
            <h1 className="mt-2 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em] md:text-5xl">
              Изменения по отслеживаемым объектам
            </h1>
          </div>
          <Link className="rounded-full bg-[linear-gradient(135deg,#0f5a48,#0d7a5f)] px-5 py-3 text-center text-sm font-bold text-white" href="/dashboard">
            Назад в dashboard
          </Link>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          {items.map((item) => (
            <article key={item.name} className="rounded-[28px] border border-[color:var(--border)] bg-white/82 p-6">
              <strong className="block text-xl">{item.name}</strong>
              <p className="mt-4 text-sm text-[var(--muted)]">Изменение</p>
              <strong className="mt-1 block text-lg">{item.delta}</strong>
              <p className="mt-5 text-sm text-[var(--muted)]">Статус очереди</p>
              <strong className="mt-1 block">{item.state}</strong>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
