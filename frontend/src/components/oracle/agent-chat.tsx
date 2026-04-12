"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { AgentMascot } from "./agent-mascot";
import { ScoreGauge } from "./score-gauge";

type StepMessage = { type: "step"; text: string };
type AnalysisChunk = { type: "analysis"; text: string };
type VerdictMessage = {
  type: "verdict";
  score: number;
  risk_level: string;
  reasoning: string;
};
type ErrorMessage = { type: "error"; text: string };
type DeployerTokenEntry = {
  mint: string;
  name: string;
  symbol: string;
  rug_probability: number;
  risk_level: string;
};
type DeployerMessage = {
  type: "deployer";
  deployer_wallet: string;
  total_launches: number;
  rug_count: number;
  rug_ratio: number;
  avg_rug_probability: number;
  risk_label: string;
  recent_tokens: DeployerTokenEntry[];
  from_db: boolean;
};
type SSEMessage = StepMessage | AnalysisChunk | VerdictMessage | ErrorMessage | DeployerMessage;

function riskColor(level: string) {
  switch (level) {
    case "low":
      return "text-emerald-400 border-emerald-400/30 bg-emerald-400/10";
    case "medium":
      return "text-amber-400 border-amber-400/30 bg-amber-400/10";
    case "high":
      return "text-orange-400 border-orange-400/30 bg-orange-400/10";
    case "critical":
      return "text-rose-400 border-rose-400/30 bg-rose-400/10";
    default:
      return "text-slate-400 border-slate-400/30 bg-slate-400/10";
  }
}

function scoreColor(score: number) {
  if (score <= 25) return "text-emerald-400";
  if (score <= 50) return "text-amber-400";
  if (score <= 75) return "text-orange-400";
  return "text-rose-400";
}

function scoreBgGlow(score: number) {
  if (score <= 25) return "shadow-[0_0_30px_rgba(52,211,153,0.15)]";
  if (score <= 50) return "shadow-[0_0_30px_rgba(251,191,36,0.15)]";
  if (score <= 75) return "shadow-[0_0_30px_rgba(249,115,22,0.15)]";
  return "shadow-[0_0_30px_rgba(244,63,94,0.2)]";
}

function scoreBarColor(score: number) {
  if (score <= 25) return "bg-gradient-to-r from-emerald-500 to-emerald-400";
  if (score <= 50) return "bg-gradient-to-r from-amber-500 to-amber-400";
  if (score <= 75) return "bg-gradient-to-r from-orange-500 to-orange-400";
  return "bg-gradient-to-r from-rose-600 to-rose-400";
}

function formatAnalysis(text: string) {
  const clean = text.replace(/\{[^{}]*"score"[^{}]*\}\s*$/, "").trim();
  return clean.split("\n").map((line, i) => {
    const trimmed = line.trim();
    if (!trimmed) return <br key={i} />;
    if (trimmed.startsWith("###")) {
      return (
        <div key={i} className="mt-3 mb-1 text-xs font-bold uppercase tracking-wider text-cyan-400">
          {trimmed.replace(/^#+\s*/, "")}
        </div>
      );
    }
    const parts = trimmed.split(/(\*\*[^*]+\*\*)/g);
    return (
      <div key={i}>
        {parts.map((part, j) =>
          part.startsWith("**") && part.endsWith("**") ? (
            <span key={j} className="font-semibold text-slate-200">
              {part.slice(2, -2)}
            </span>
          ) : (
            <span key={j}>{part}</span>
          ),
        )}
      </div>
    );
  });
}

export function AgentChat() {
  const [address, setAddress] = useState("");
  const [steps, setSteps] = useState<string[]>([]);
  const [analysisText, setAnalysisText] = useState("");
  const [verdict, setVerdict] = useState<VerdictMessage | null>(null);
  const [deployer, setDeployer] = useState<DeployerMessage | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [, setDone] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [steps, analysisText, verdict, error]);

  const handleAnalyze = useCallback(async () => {
    const trimmed = address.trim();
    if (!trimmed || running) return;

    setSteps([]);
    setAnalysisText("");
    setVerdict(null);
    setDeployer(null);
    setError("");
    setDone(false);
    setRunning(true);

    abortRef.current = new AbortController();

    try {
      const res = await fetch("/api/v1/oracle/agent/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token_address: trimmed }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        setError(`Request failed: ${res.status}`);
        setRunning(false);
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done: readerDone, value } = await reader.read();
        if (readerDone) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6).trim();
          if (payload === "[DONE]") {
            setDone(true);
            setRunning(false);
            return;
          }

          try {
            const msg: SSEMessage = JSON.parse(payload);
            switch (msg.type) {
              case "step":
                setSteps((prev) => [...prev, msg.text]);
                break;
              case "analysis":
                setAnalysisText((prev) => prev + msg.text);
                break;
              case "verdict":
                setVerdict(msg);
                break;
              case "deployer":
                setDeployer(msg);
                break;
              case "error":
                setError(msg.text);
                break;
            }
          } catch {
            // skip
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setError((err as Error).message || "Connection failed");
      }
    }

    setRunning(false);
    setDone(true);
  }, [address, running]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAnalyze();
    }
  };

  const scrollToSection = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  const hasContent = steps.length > 0 || analysisText || verdict || deployer || error;
  const mascotState = running ? "scanning" : verdict ? (verdict.score >= 75 ? "alert" : "idle") : "idle";

  return (
    <section className="overflow-hidden rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)]">
      {/* Header with mascot */}
      <div className="flex items-center gap-4 border-b border-[rgba(59,130,246,0.1)] bg-[rgba(59,130,246,0.04)] px-4 py-3 sm:px-6 sm:py-4">
        <AgentMascot state={mascotState} size="sm" />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-slate-100">AI Agent</h2>
            <div className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </div>
            <span className="text-[10px] font-medium text-emerald-400">Online</span>
          </div>
          <p className="text-[11px] text-slate-500">
            {running ? "Scanning token..." : "Rule Engine + XGBoost ML + GPT-4o-mini"}
          </p>
        </div>
        {running && (
          <div className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1">
            <svg className="h-3 w-3 animate-spin text-emerald-400" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
              <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className="opacity-75" />
            </svg>
            <span className="text-[10px] font-bold text-emerald-400">ANALYZING</span>
          </div>
        )}
      </div>

      <div className="p-4 sm:p-6">
        {/* Input row */}
        <div className="mb-4 flex flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <svg
              className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Paste Solana token address..."
              disabled={running}
              className="w-full rounded-xl border border-[rgba(59,130,246,0.2)] bg-[rgba(2,6,23,0.6)] py-3 pl-10 pr-4 text-sm text-slate-100 placeholder-slate-500 outline-none transition-all focus:border-[#3b82f6]/50 focus:shadow-[0_0_20px_rgba(59,130,246,0.1)] disabled:opacity-50"
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={running || !address.trim()}
            className="group relative overflow-hidden rounded-xl bg-[linear-gradient(135deg,#2563eb,#06b6d4)] px-6 py-3 text-sm font-bold text-white shadow-[0_12px_24px_rgba(37,99,235,0.25)] transition-all hover:shadow-[0_16px_32px_rgba(37,99,235,0.35)] hover:brightness-110 disabled:opacity-50"
          >
            <span className="relative z-10 flex items-center gap-2">
              {running ? (
                <>
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
                    <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className="opacity-75" />
                  </svg>
                  Analyzing
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                  </svg>
                  Analyze
                </>
              )}
            </span>
          </button>
        </div>

        {/* Messages area */}
        {hasContent && (
          <div
            ref={scrollRef}
            className="max-h-[60vh] overflow-y-auto rounded-xl border border-[rgba(59,130,246,0.1)] bg-[rgba(2,6,23,0.5)] p-3 sm:max-h-[480px] sm:p-4"
          >
            {/* Steps */}
            {steps.map((text, i) => (
              <div
                key={i}
                className="animate-fade-in-up mb-2 flex items-start gap-2.5"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <span className="mt-1.5 inline-block h-2 w-2 flex-shrink-0 rounded-full bg-emerald-500" />
                <span className="text-sm text-slate-400">{text}</span>
              </div>
            ))}

            {/* Analysis text */}
            {analysisText && (
              <div className="mt-3 border-t border-slate-700/50 pt-3">
                <div className="mb-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-cyan-400">
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023.501.05.75.082M19 14.5l-2.47 2.47a2.25 2.25 0 01-1.591.659H9.061a2.25 2.25 0 01-1.591-.659L5 14.5m14 0V17a2.25 2.25 0 01-2.25 2.25H7.25A2.25 2.25 0 015 17v-2.5" />
                  </svg>
                  Agent Analysis
                </div>
                <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
                  {formatAnalysis(analysisText)}
                  {running && (
                    <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-cyan-400" />
                  )}
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="mt-3 rounded-lg border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-300">
                {error}
              </div>
            )}

                {/* Deployer DNA card */}
                {deployer && (
                  <div className="mt-3 rounded-xl border border-slate-700/40 bg-[rgba(15,23,42,0.7)] p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-400">
                        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 9h3.75M15 12h3.75M15 15h3.75M4.5 19.5h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5zm6-10.125a1.875 1.875 0 11-3.75 0 1.875 1.875 0 013.75 0zm1.294 6.336a6.721 6.721 0 01-3.17.789 6.721 6.721 0 01-3.168-.789 3.376 3.376 0 016.338 0z" />
                        </svg>
                        Deployer DNA
                      </span>
                      <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase ${
                        deployer.risk_label === "serial_rugger"
                          ? "border-rose-400/30 bg-rose-400/10 text-rose-400"
                          : deployer.risk_label === "suspicious"
                          ? "border-amber-400/30 bg-amber-400/10 text-amber-400"
                          : deployer.risk_label === "clean"
                          ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-400"
                          : "border-slate-600/30 bg-slate-600/10 text-slate-400"
                      }`}>
                        {deployer.risk_label.replace("_", " ")}
                      </span>
                    </div>
                    <div className="mb-2 font-mono text-[11px] text-slate-500">
                      {deployer.deployer_wallet.slice(0, 6)}...{deployer.deployer_wallet.slice(-4)}
                    </div>
                    {deployer.from_db && deployer.total_launches > 0 ? (
                      <div className="flex flex-wrap items-center gap-4 text-xs">
                        <div className="text-center">
                          <div className="font-bold text-slate-200">{deployer.total_launches}</div>
                          <div className="text-slate-500">launches</div>
                        </div>
                        <div className="text-center">
                          <div className={`font-bold ${deployer.rug_count > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                            {deployer.rug_count}
                          </div>
                          <div className="text-slate-500">rugs</div>
                        </div>
                        <div className="text-center">
                          <div className={`font-bold ${deployer.rug_ratio >= 0.5 ? "text-rose-400" : deployer.rug_ratio >= 0.2 ? "text-amber-400" : "text-emerald-400"}`}>
                            {Math.round(deployer.rug_ratio * 100)}%
                          </div>
                          <div className="text-slate-500">rug rate</div>
                        </div>
                        {deployer.recent_tokens.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {deployer.recent_tokens.slice(0, 3).map((t) => (
                              <span
                                key={t.mint}
                                className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                                  t.rug_probability >= 0.65
                                    ? "bg-rose-400/10 text-rose-400"
                                    : "bg-slate-700/60 text-slate-400"
                                }`}
                              >
                                ${t.symbol}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500">First time seen — no prior launch history in database.</p>
                    )}
                  </div>
                )}

            {/* Verdict card */}
            {verdict && (
              <div className={`mt-4 rounded-xl border border-[rgba(59,130,246,0.2)] bg-[rgba(15,23,42,0.95)] p-5 ${scoreBgGlow(verdict.score)}`}>
                <div className="mb-4 flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-[#60a5fa]">
                    Final Verdict
                  </span>
                  <span className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase ${riskColor(verdict.risk_level)}`}>
                    {verdict.risk_level}
                  </span>
                </div>

                <div className="mb-4 flex items-center gap-5">
                  {/* Score gauge */}
                  <div className="flex flex-col items-center">
                    <ScoreGauge score={verdict.score} size={100} />
                    <div className="mt-1 text-[10px] text-slate-500">/ 100</div>
                  </div>
                  {verdict.reasoning && (
                    <p className="flex-1 text-sm leading-relaxed text-slate-400">
                      {verdict.reasoning}
                    </p>
                  )}
                </div>

                {/* Action buttons */}
                <div className="flex flex-col gap-2 sm:flex-row">
                  <button
                    onClick={() => scrollToSection("oracle-add-token")}
                    className="flex-1 rounded-xl border border-[rgba(59,130,246,0.3)] bg-[rgba(59,130,246,0.08)] px-4 py-2.5 text-xs font-semibold text-[#60a5fa] transition-all hover:bg-[rgba(59,130,246,0.15)] hover:shadow-[0_0_20px_rgba(59,130,246,0.1)]"
                  >
                    Add to Monitor
                  </button>
                  <button
                    onClick={() => scrollToSection("guarded-vault")}
                    className="flex-1 rounded-xl bg-[linear-gradient(135deg,#2563eb,#06b6d4)] px-4 py-2.5 text-xs font-bold text-white shadow-[0_8px_16px_rgba(37,99,235,0.2)] transition-all hover:shadow-[0_12px_24px_rgba(37,99,235,0.3)] hover:brightness-110"
                  >
                    Protect with GuardedVault
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty state with mascot */}
        {!hasContent && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700/40 bg-[rgba(2,6,23,0.3)] py-10 text-center sm:py-14">
            <AgentMascot state="idle" size="lg" />
            <h3 className="mt-5 text-base font-bold text-slate-200">
              Ready to analyze
            </h3>
            <p className="mt-2 max-w-sm text-sm text-slate-500">
              Paste a Solana token address and hit{" "}
              <span className="font-semibold text-cyan-400">Analyze</span> — the AI agent will
              inspect on-chain data and stream findings in real-time
            </p>
            <div className="mt-4 flex items-center gap-3 text-[10px] text-slate-600">
              <span className="flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-cyan-500/50" />
                56 features
              </span>
              <span className="flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-blue-500/50" />
                ML model
              </span>
              <span className="flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-purple-500/50" />
                GPT-4o-mini
              </span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
