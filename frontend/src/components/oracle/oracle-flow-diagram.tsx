export function OracleFlowDiagram() {
  return (
    <section className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-6">
      <h2 className="mb-4 text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">
        AI &rarr; On-Chain Pipeline
      </h2>

      <div className="flex flex-wrap items-center justify-center gap-3 py-4 text-sm">
        {/* Step 1: AI Scoring */}
        <div className="flex flex-col items-center gap-1.5 rounded-2xl border border-[#3b82f6]/20 bg-[#3b82f6]/8 px-5 py-4 text-center">
          <span className="text-2xl">🧠</span>
          <span className="font-bold text-slate-100">AI Scoring</span>
          <span className="text-xs text-slate-400">ML + 50 features</span>
        </div>

        <Arrow />

        {/* Step 2: Decision */}
        <div className="flex flex-col items-center gap-1.5 rounded-2xl border border-amber-400/20 bg-amber-400/8 px-5 py-4 text-center">
          <span className="text-2xl">⚡</span>
          <span className="font-bold text-slate-100">Risk Decision</span>
          <span className="text-xs text-slate-400">score 0-100</span>
        </div>

        <Arrow />

        {/* Step 3: On-chain TX */}
        <div className="flex flex-col items-center gap-1.5 rounded-2xl border border-emerald-400/20 bg-emerald-400/8 px-5 py-4 text-center">
          <span className="text-2xl">📝</span>
          <span className="font-bold text-slate-100">Solana TX</span>
          <span className="text-xs text-slate-400">publish_score()</span>
        </div>

        <Arrow />

        {/* Step 4: State Change */}
        <div className="flex flex-col items-center gap-1.5 rounded-2xl border border-violet-400/20 bg-violet-400/8 px-5 py-4 text-center">
          <span className="text-2xl">🔗</span>
          <span className="font-bold text-slate-100">On-Chain State</span>
          <span className="text-xs text-slate-400">PDA updated</span>
        </div>

        <Arrow />

        {/* Step 5: Vault Guard */}
        <div className="flex flex-col items-center gap-1.5 rounded-2xl border border-rose-400/20 bg-rose-400/8 px-5 py-4 text-center">
          <span className="text-2xl">🛡️</span>
          <span className="font-bold text-slate-100">Vault Guard</span>
          <span className="text-xs text-slate-400">block risky swaps</span>
        </div>
      </div>
    </section>
  );
}

function Arrow() {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      className="shrink-0 text-[#3b82f6]/40"
    >
      <path
        d="M5 12h14m0 0l-4-4m4 4l-4 4"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
