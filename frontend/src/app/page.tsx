const coverageItems = [
  {
    title: "Token",
    description:
      "Анализ authority, supply, holder concentration, liquidity и token metadata.",
    bullets: [
      "Mint authority / freeze authority",
      "Age, volume, liquidity",
      "Holder concentration",
    ],
  },
  {
    title: "Wallet",
    description:
      "Проверка связей с flagged адресами, rug-паттернов и deployer behavior.",
    bullets: [
      "Связи с suspicious entities",
      "Transaction patterns",
      "Launch-dump behavior",
    ],
  },
  {
    title: "Project",
    description:
      "Агрегация token, domain, socials и manual moderation в единый risk profile.",
    bullets: [
      "Domain age and trust",
      "Social validation",
      "Aggregated risk summary",
    ],
  },
];

const workflowSteps = [
  {
    step: "01",
    title: "Fast analysis",
    description: "Быстрый первичный risk score на базе ончейн- и external signals.",
  },
  {
    step: "02",
    title: "Explainability layer",
    description: "Каждый verdict раскладывается на rule hits, severity и evidence.",
  },
  {
    step: "03",
    title: "Background refresh",
    description: "Глубокий пересчет уточняет отчет без потери первичного ответа.",
  },
];

const topFindings = [
  {
    severity: "HIGH",
    title: "Mint authority активна",
    description: "Supply токена можно изменить после запуска.",
  },
  {
    severity: "HIGH",
    title: "87% у top 10 holders",
    description: "Критичная концентрация предложения у ограниченного круга адресов.",
  },
  {
    severity: "MEDIUM",
    title: "Новый домен проекта",
    description: "Связанный сайт зарегистрирован менее 14 дней назад.",
  },
];

const trustItems = [
  {
    title: "Explainable scoring",
    description: "Пользователь видит не только label, но и список причин, почему он получен.",
  },
  {
    title: "Freshness awareness",
    description: "Интерфейс явно показывает свежесть данных и активный background refresh.",
  },
  {
    title: "Human moderation ready",
    description: "UI уже готов к manual labels, review queue и работе аналитиков.",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <div className="mx-auto w-full max-w-[1240px] px-5 py-6 md:px-8 md:py-8">
        <header className="mb-7 flex flex-col gap-5 rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] px-5 py-5 shadow-[0_18px_60px_rgba(20,34,27,0.08)] backdrop-blur md:flex-row md:items-center md:justify-between">
          <a className="flex items-center gap-4" href="#top">
            <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[linear-gradient(135deg,#14392f,#0d7a5f)] font-[family:var(--font-display)] text-lg font-bold text-white">
              S
            </span>
            <span className="flex flex-col">
              <strong className="text-sm font-extrabold tracking-[-0.03em]">
                Solace Scan
              </strong>
              <span className="text-xs text-[var(--muted)]">
                Solana risk intelligence
              </span>
            </span>
          </a>

          <nav className="flex flex-wrap gap-4 text-sm text-[var(--muted)] md:justify-center">
            <a href="#coverage">Что проверяем</a>
            <a href="#workflow">Как работает</a>
            <a href="#report">Отчет</a>
            <a href="#trust">Почему нам верят</a>
          </nav>

            <div className="flex flex-col gap-3 sm:flex-row">
              <a
                className="rounded-full border border-[color:var(--border)] bg-white/70 px-5 py-3 text-center text-sm font-bold"
                href="/dashboard"
              >
                Открыть dashboard
              </a>
              <a
                className="rounded-full bg-[linear-gradient(135deg,#0f5a48,#0d7a5f)] px-5 py-3 text-center text-sm font-bold text-white shadow-[0_18px_36px_rgba(13,122,95,0.22)]"
                href="/report/token/pearl-token"
              >
                Demo result page
              </a>
            </div>
        </header>

        <section
          id="top"
          className="grid items-center gap-8 py-5 md:grid-cols-[1.04fr_0.96fr] md:py-10"
        >
          <div>
            <p className="text-xs font-extrabold tracking-[0.22em] text-[var(--accent-deep)]">
              SCAM CHECK FOR SOLANA
            </p>
            <h1 className="mt-3 max-w-[11ch] font-[family:var(--font-display)] text-5xl leading-[0.95] font-bold tracking-[-0.06em] md:text-7xl">
              Проверяй токены и кошельки до того, как они проверят тебя
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-[var(--muted)] md:text-lg">
              Solace Scan показывает risk score, ключевые факторы риска и свежесть
              данных по токенам, проектам и кошелькам в сети Solana. Быстрый verdict
              наверху, подробный разбор ниже.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              {[
                ["3", "типа сущностей"],
                ["< 8 сек", "первичный анализ"],
                ["Explainable", "каждый score"],
              ].map(([value, label]) => (
                <div
                  key={label}
                  className="min-w-36 rounded-3xl border border-[color:var(--border)] bg-white/75 px-5 py-4"
                >
                  <strong className="block text-lg font-extrabold">{value}</strong>
                  <span className="text-sm text-[var(--muted)]">{label}</span>
                </div>
              ))}
            </div>

            <div
              id="check"
              className="mt-7 flex flex-col gap-3 rounded-[28px] border border-[color:var(--border)] bg-white/85 p-3 shadow-[0_24px_80px_rgba(29,39,33,0.14)] md:flex-row"
            >
              <input
                defaultValue="9xQeWvG816bUx9EPfEZLQ7ZL8A6V7zVYhWf9e7s6PzF1"
                className="min-w-0 flex-1 rounded-2xl border border-transparent bg-transparent px-4 py-4 text-sm outline-none placeholder:text-[var(--muted)]"
                placeholder="Вставь token mint, wallet или URL проекта"
                type="text"
              />
              <button className="rounded-3xl bg-[linear-gradient(135deg,#b43f28,#db6b4f)] px-6 py-4 text-sm font-extrabold text-white">
                Запустить проверку
              </button>
            </div>

            <p className="mt-3 text-sm text-[var(--muted)]">
              Поддерживаются токены, кошельки и project-level проверки для Solana.
            </p>
          </div>

          <div className="relative min-h-[560px]">
            <div className="absolute right-4 top-8 h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle_at_30%_30%,rgba(255,255,255,0.96),rgba(255,255,255,0.08)_35%),linear-gradient(135deg,rgba(13,122,95,0.18),rgba(200,75,49,0.11))] blur-md" />
            <article className="relative ml-auto flex max-w-[520px] flex-col rounded-[32px] border border-[color:var(--border)] bg-white/85 p-6 shadow-[0_24px_80px_rgba(29,39,33,0.14)] backdrop-blur">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-xs font-extrabold tracking-[0.18em] text-[var(--accent-deep)]">
                    Последний анализ
                  </p>
                  <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em]">
                    PEARL / Solana meme token
                  </h2>
                </div>
                <span className="w-fit rounded-full bg-[linear-gradient(135deg,#a9341e,#c84b31)] px-4 py-2 text-sm font-extrabold text-white">
                  Critical risk
                </span>
              </div>

              <div className="mt-6 flex flex-col gap-5 md:flex-row md:items-center">
                <div className="grid h-30 w-30 place-items-center rounded-full bg-[radial-gradient(circle_closest-side,#fff_67%,transparent_68%_100%),conic-gradient(#c84b31_0_82%,rgba(200,75,49,0.14)_82%_100%)]">
                  <span className="font-[family:var(--font-display)] text-4xl font-bold">
                    82
                  </span>
                </div>
                <div className="flex-1">
                  <p className="text-sm text-[var(--muted)]">Итоговый risk score</p>
                  <strong className="mt-2 block text-base leading-7">
                    Причины: mint authority, concentration, suspicious deployer
                  </strong>
                  <span className="mt-2 block text-sm text-[var(--muted)]">
                    Обновлено 4 минуты назад
                  </span>
                </div>
              </div>

              <div className="mt-6 grid gap-3 md:grid-cols-3">
                {topFindings.map((item) => (
                  <article
                    key={item.title}
                    className="rounded-3xl border border-[color:var(--border)] bg-[rgba(244,241,232,0.72)] p-4"
                  >
                    <span className="text-[11px] font-extrabold tracking-[0.16em] text-[var(--critical)]">
                      {item.severity}
                    </span>
                    <strong className="mt-2 block leading-6">{item.title}</strong>
                    <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                      {item.description}
                    </p>
                  </article>
                ))}
              </div>

              <div className="mt-5 grid gap-4 border-t border-[color:var(--border)] pt-5 md:grid-cols-3">
                {[
                  ["Confidence", "0.81"],
                  ["Liquidity", "$12.4K"],
                  ["Review queue", "Escalated"],
                ].map(([label, value]) => (
                  <div key={label}>
                    <span className="text-sm text-[var(--muted)]">{label}</span>
                    <strong className="mt-1 block">{value}</strong>
                  </div>
                ))}
              </div>
            </article>
          </div>
        </section>

        <section className="mt-2 flex flex-col gap-5 rounded-[28px] border border-[color:var(--border)] bg-[var(--surface)] px-6 py-6 md:flex-row md:items-center md:justify-between">
          <p className="font-bold">
            Для ресерча, модерации и быстрой проверки перед покупкой
          </p>
          <div className="flex flex-wrap gap-3">
            {["Token scan", "Wallet intelligence", "Project verification", "Rule-based scoring"].map(
              (item) => (
                <span
                  key={item}
                  className="rounded-full bg-[rgba(13,122,95,0.08)] px-4 py-2 text-sm font-bold text-[var(--accent-deep)]"
                >
                  {item}
                </span>
              ),
            )}
          </div>
        </section>

        <section
          id="coverage"
          className="mt-7 rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] px-6 py-8 md:px-8 md:py-9"
        >
          <div className="max-w-3xl">
            <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
              ОХВАТ ПРОВЕРКИ
            </p>
            <h2 className="mt-3 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em] md:text-6xl">
              Один поиск, три типа риска
            </h2>
            <p className="mt-4 text-base leading-8 text-[var(--muted)]">
              Главный сценарий строится вокруг одной строки поиска. Система сама
              определяет сущность и собирает explainable отчет.
            </p>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {coverageItems.map((item) => (
              <article
                key={item.title}
                className="rounded-[28px] border border-[color:var(--border)] bg-white/80 p-6 shadow-[0_12px_32px_rgba(22,31,26,0.06)]"
              >
                <div className="h-14 w-14 rounded-2xl bg-[linear-gradient(135deg,rgba(13,122,95,0.18),rgba(16,35,26,0.04))]" />
                <h3 className="mt-4 text-xl font-bold">{item.title}</h3>
                <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
                  {item.description}
                </p>
                <ul className="mt-5 list-disc space-y-2 pl-5 text-sm leading-7 text-[var(--muted)]">
                  {item.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section
          id="workflow"
          className="mt-7 grid gap-6 rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] px-6 py-8 md:grid-cols-[0.86fr_1.14fr] md:px-8 md:py-9"
        >
          <div className="max-w-xl">
            <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
              КАК ЭТО РАБОТАЕТ
            </p>
            <h2 className="mt-3 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em] md:text-6xl">
              Не просто label, а понятный разбор
            </h2>
            <p className="mt-4 text-base leading-8 text-[var(--muted)]">
              Пользователь получает verdict сверху, но может быстро дойти до
              доказательств: какие сигналы сработали, насколько свежи данные, и что
              именно вызывает риск.
            </p>
          </div>

          <div className="grid gap-4">
            {workflowSteps.map((item) => (
              <article
                key={item.step}
                className="grid gap-4 rounded-[28px] border border-[color:var(--border)] bg-white/75 p-5 md:grid-cols-[72px_1fr]"
              >
                <span className="grid h-13 w-13 place-items-center rounded-2xl bg-[linear-gradient(135deg,#0f5a48,#0d7a5f)] font-[family:var(--font-display)] text-lg font-bold text-white">
                  {item.step}
                </span>
                <div>
                  <h3 className="text-xl font-bold">{item.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-[var(--muted)]">
                    {item.description}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section
          id="report"
          className="mt-7 rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] px-6 py-8 md:px-8 md:py-9"
        >
          <div className="max-w-3xl">
            <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
              RESULT EXPERIENCE
            </p>
            <h2 className="mt-3 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em] md:text-6xl">
              Report page, которую можно прочитать за 10 секунд
            </h2>
            <p className="mt-4 text-base leading-8 text-[var(--muted)]">
              Above-the-fold зона дает итоговое решение, confidence и топ-факторы
              риска. Ниже лежат holders, liquidity, links и history.
            </p>
          </div>

          <div className="mt-8 grid gap-4 rounded-[32px] border border-[color:var(--border)] p-4 md:grid-cols-[280px_1fr]">
            <aside className="rounded-[28px] bg-white/82 p-6">
              <p className="text-xs font-extrabold tracking-[0.18em] text-[var(--accent-deep)]">
                Summary
              </p>
              <h3 className="mt-3 text-2xl font-bold">Scam check result</h3>
              <ul className="mt-5 list-disc space-y-2 pl-5 text-sm leading-7 text-[var(--muted)]">
                <li>Score + status</li>
                <li>Confidence</li>
                <li>Top findings</li>
                <li>Refresh state</li>
              </ul>
            </aside>

            <div className="rounded-[28px] bg-white/82 p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-xs font-extrabold tracking-[0.18em] text-[var(--accent-deep)]">
                    Token report
                  </p>
                  <h3 className="mt-2 text-2xl font-bold">PEARL / 9xQe...PzF1</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full bg-[rgba(13,122,95,0.08)] px-4 py-2 text-sm font-bold text-[var(--accent-deep)]">
                    Solana
                  </span>
                  <span className="rounded-full bg-[rgba(201,142,41,0.14)] px-4 py-2 text-sm font-bold text-[#8f671d]">
                    High priority
                  </span>
                </div>
              </div>

              <div className="mt-6 grid gap-3 md:grid-cols-4">
                {[
                  ["Score", "82"],
                  ["Confidence", "0.81"],
                  ["Top 10 share", "87.4%"],
                  ["Liquidity", "$12.4K"],
                ].map(([label, value]) => (
                  <article
                    key={label}
                    className="rounded-3xl bg-[rgba(244,241,232,0.72)] px-4 py-4"
                  >
                    <span className="text-sm text-[var(--muted)]">{label}</span>
                    <strong className="mt-2 block text-lg">{value}</strong>
                  </article>
                ))}
              </div>

              <div className="mt-4 grid gap-3">
                {[
                  ["Active mint authority", "Detected", "danger"],
                  ["Linked deployer history", "3 suspicious launches", "danger"],
                  ["Project domain age", "12 days", "warn"],
                  ["Background refresh", "In progress", "neutral"],
                ].map(([label, value, tone]) => (
                  <div
                    key={label}
                    className="flex flex-col gap-2 rounded-3xl bg-[rgba(244,241,232,0.72)] px-4 py-4 md:flex-row md:items-center md:justify-between"
                  >
                    <span className="text-sm text-[var(--muted)]">{label}</span>
                    <strong
                      className={
                        tone === "danger"
                          ? "text-[var(--critical)]"
                          : tone === "warn"
                            ? "text-[#99660e]"
                            : "text-[var(--foreground)]"
                      }
                    >
                      {value}
                    </strong>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section
          id="trust"
          className="mt-7 rounded-[32px] border border-[color:var(--border)] bg-[linear-gradient(135deg,rgba(13,122,95,0.06),rgba(255,255,255,0.72))] p-6 md:p-8"
        >
          <div className="grid gap-6 md:grid-cols-[0.9fr_1.1fr]">
            <div className="max-w-xl">
              <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
                ПОЧЕМУ ЭТОТ UX РАБОТАЕТ
              </p>
              <h2 className="mt-3 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em] md:text-6xl">
                Минимум крика, максимум сигнала
              </h2>
              <p className="mt-4 text-base leading-8 text-[var(--muted)]">
                Дизайн не маскирует risk data. Он помогает быстро принять решение и
                отдельно помечает, где данных недостаточно или verdict еще
                уточняется.
              </p>
            </div>

            <div className="grid gap-4">
              {trustItems.map((item) => (
                <article
                  key={item.title}
                  className="rounded-3xl border border-[color:var(--border)] bg-white/80 p-5"
                >
                  <strong className="block text-lg">{item.title}</strong>
                  <p className="mt-2 text-sm leading-7 text-[var(--muted)]">
                    {item.description}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-7 flex flex-col gap-6 rounded-[32px] border border-[color:var(--border)] bg-[var(--surface)] px-6 py-8 md:flex-row md:items-center md:justify-between md:px-8">
          <div>
            <p className="text-xs font-extrabold tracking-[0.2em] text-[var(--accent-deep)]">
              START WITH A SINGLE CHECK
            </p>
            <h2 className="mt-3 max-w-[16ch] font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em] md:text-6xl">
              Готово как посадочная страница для продукта и как база для app dashboard
            </h2>
          </div>
          <a
            className="rounded-full bg-[linear-gradient(135deg,#0f5a48,#0d7a5f)] px-6 py-4 text-center text-sm font-bold text-white shadow-[0_18px_36px_rgba(13,122,95,0.22)]"
            href="/dashboard"
          >
            Открыть dashboard
          </a>
        </section>
      </div>
    </main>
  );
}
