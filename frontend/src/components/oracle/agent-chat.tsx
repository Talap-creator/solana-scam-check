"use client";

import { useState, useRef, useCallback, useEffect } from "react";

type StepMessage = { type: "step"; text: string };
type AnalysisChunk = { type: "analysis"; text: string };
type VerdictMessage = {
  type: "verdict";
  score: number;
  risk_level: string;
  reasoning: string;
};
type ErrorMessage = { type: "error"; text: string };
type SSEMessage = StepMessage | AnalysisChunk | VerdictMessage | ErrorMessage;

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

function formatAnalysis(text: string) {
  // Remove trailing JSON block
  let clean = text.replace(/\{[^{}]*"score"[^{}]*\}\s*$/, "").trim();
  // Split into lines and format
  return clean.split("\n").map((line, i) => {
    const trimmed = line.trim();
    if (!trimmed) return <br key={i} />;
    // ### headings
    if (trimmed.startsWith("###")) {
      return <div key={i} className="mt-3 mb-1 text-xs font-bold uppercase tracking-wider text-cyan-400">{trimmed.replace(/^#+\s*/, "")}</div>;
    }
    // **bold** inline
    const parts = trimmed.split(/(\*\*[^*]+\*\*)/g);
    return (
      <div key={i}>
        {parts.map((part, j) =>
          part.startsWith("**") && part.endsWith("**")
            ? <span key={j} className="font-semibold text-slate-200">{part.slice(2, -2)}</span>
            : <span key={j}>{part}</span>
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
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [steps, analysisText, verdict, error]);

  const handleAnalyze = useCallback(async () => {
    const trimmed = address.trim();
    if (!trimmed || running) return;

    // Reset state
    setSteps([]);
    setAnalysisText("");
    setVerdict(null);
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
              case "error":
                setError(msg.text);
                break;
            }
          } catch {
            // skip unparseable lines
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

  const hasContent = steps.length > 0 || analysisText || verdict || error;

  return (
    <section className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-4 sm:p-6">
      {/* Header */}
      <div className="mb-4 flex items-center gap-3">
        <div className="relative flex h-3 w-3">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500" />
        </div>
        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">
          AI Agent
        </h2>
        <span className="text-[10px] text-slate-500">
          Powered by RugSignal Intelligence
        </span>
      </div>

      {/* Input row */}
      <div className="mb-4 flex flex-col gap-2 sm:flex-row">
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Paste token address to analyze..."
          disabled={running}
          className="flex-1 rounded-lg border border-[rgba(59,130,246,0.2)] bg-[rgba(2,6,23,0.6)] px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition-colors focus:border-[#3b82f6]/50 disabled:opacity-50"
        />
        <button
          onClick={handleAnalyze}
          disabled={running || !address.trim()}
          className="relative overflow-hidden rounded-lg bg-[linear-gradient(135deg,#2563eb,#06b6d4)] px-5 py-2.5 text-sm font-bold text-white shadow-[0_12px_24px_rgba(37,99,235,0.25)] transition-all hover:brightness-110 disabled:opacity-50"
        >
          {running ? (
            <span className="flex items-center gap-2">
              <svg
                className="h-4 w-4 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="3"
                  className="opacity-25"
                />
                <path
                  d="M4 12a8 8 0 018-8"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                  className="opacity-75"
                />
              </svg>
              Analyzing
            </span>
          ) : (
            "Analyze"
          )}
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
            <div key={i} className="mb-2 flex items-start gap-2.5">
              <span className="mt-1.5 inline-block h-2 w-2 flex-shrink-0 rounded-full bg-emerald-500" />
              <span className="text-sm text-slate-400">{text}</span>
            </div>
          ))}

          {/* Analysis text */}
          {analysisText && (
            <div className="mt-3 border-t border-slate-700/50 pt-3">
              <div className="mb-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-cyan-400">
                <svg
                  className="h-3.5 w-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023.501.05.75.082M19 14.5l-2.47 2.47a2.25 2.25 0 01-1.591.659H9.061a2.25 2.25 0 01-1.591-.659L5 14.5m14 0V17a2.25 2.25 0 01-2.25 2.25H7.25A2.25 2.25 0 015 17v-2.5"
                  />
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

          {/* Verdict card */}
          {verdict && (
            <div className="mt-4 rounded-xl border border-[rgba(59,130,246,0.2)] bg-[rgba(15,23,42,0.9)] p-4">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#60a5fa]">
                  Final Verdict
                </span>
                <span
                  className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase ${riskColor(verdict.risk_level)}`}
                >
                  {verdict.risk_level}
                </span>
              </div>

              <div className="mb-3 flex items-center gap-4">
                <div className="text-center">
                  <div
                    className={`text-3xl font-black tabular-nums ${scoreColor(verdict.score)}`}
                  >
                    {verdict.score}
                  </div>
                  <div className="text-[10px] text-slate-500">RISK SCORE</div>
                </div>
                {verdict.reasoning && (
                  <p className="flex-1 text-sm text-slate-400">
                    {verdict.reasoning}
                  </p>
                )}
              </div>

              {/* Action buttons */}
              <div className="flex flex-col gap-2 sm:flex-row">
                <button
                  onClick={() => scrollToSection("oracle-add-token")}
                  className="flex-1 rounded-lg border border-[rgba(59,130,246,0.3)] bg-[rgba(59,130,246,0.1)] px-3 py-2 text-xs font-semibold text-[#60a5fa] transition-colors hover:bg-[rgba(59,130,246,0.2)]"
                >
                  Add to Monitor
                </button>
                <button
                  onClick={() => scrollToSection("guarded-vault")}
                  className="flex-1 rounded-lg bg-[linear-gradient(135deg,#2563eb,#06b6d4)] px-3 py-2 text-xs font-bold text-white transition-all hover:brightness-110"
                >
                  Protect with GuardedVault
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!hasContent && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700/50 bg-[rgba(2,6,23,0.3)] py-12 text-center">
          <div className="mb-3 text-4xl opacity-40">
            <svg
              className="mx-auto h-10 w-10 text-slate-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"
              />
            </svg>
          </div>
          <p className="text-sm text-slate-500">
            Paste a Solana token address and hit{" "}
            <span className="font-semibold text-slate-400">Analyze</span> to
            start the AI agent
          </p>
          <p className="mt-1 text-[11px] text-slate-600">
            The agent will inspect on-chain data and stream its findings in
            real-time
          </p>
        </div>
      )}
    </section>
  );
}
