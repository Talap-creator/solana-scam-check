"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { AppIcon } from "@/components/app-icon";
import { ApiError, submitCheck, type SubmitEntityType } from "@/lib/api";

const progressStops = [12, 28, 44, 68, 84];
const labels = [
  "Queueing Deep Scan",
  "Analyzing Contract Ownership",
  "Checking Liquidity Burn",
  "Scoring Risk Profile",
];

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function AnalysisLayout({
  error,
  phase,
  previewLabel,
}: {
  error: string | null;
  phase: number;
  previewLabel: string;
}) {
  return (
    <main className="min-h-screen bg-[#0a0f1e] font-[family:var(--font-sans)] text-slate-100 antialiased">
      <div className="relative flex min-h-screen flex-col overflow-x-hidden">
        <header className="sticky top-0 z-50 border-b border-[rgba(59,130,246,0.1)] bg-[rgba(10,15,30,0.82)] px-6 py-4 backdrop-blur-md md:px-20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#3b82f6] text-white">
                  <AppIcon className="h-5 w-5" name="shield" />
                </div>
                <h2 className="text-xl font-bold tracking-tight text-white">SolanaTrust</h2>
              </div>
              <nav className="hidden items-center gap-6 md:flex">
                <Link className="text-sm font-medium text-[#3b82f6]" href="/coins">
                  Launch Feed
                </Link>
              </nav>
            </div>

            <div className="flex items-center gap-4">
              <button className="flex h-10 w-10 items-center justify-center rounded-lg bg-[rgba(59,130,246,0.1)] text-[#3b82f6] transition-all hover:bg-[rgba(59,130,246,0.2)]">
                <AppIcon className="h-5 w-5" name="bell" />
              </button>
              <div className="hidden items-center gap-3 md:flex">
                <Link className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:text-[#3b82f6]" href="/login">
                  Log In
                </Link>
                <Link className="rounded-lg bg-[#3b82f6] px-4 py-2 text-sm font-bold text-white shadow-lg shadow-[#3b82f6]/20" href="/register">
                  Connect Wallet
                </Link>
              </div>
            </div>
          </div>
        </header>

        <main className="flex flex-1 flex-col items-center justify-center px-4 py-12">
          <div className="flex w-full max-w-[800px] flex-col items-center">
            <div className="group relative mb-12 flex aspect-video w-full items-center justify-center overflow-hidden rounded-2xl border border-[rgba(59,130,246,0.2)] bg-slate-900/50 md:aspect-[21/9]">
              <div className="pointer-events-none absolute inset-0 opacity-20 [background:radial-gradient(circle_at_center,rgba(59,130,246,0.3),transparent_60%)]" />
              <div className="pointer-events-none absolute inset-0 bg-[length:100%_4px] [background-image:linear-gradient(to_bottom,transparent_0%,rgba(59,130,246,0.05)_50%,transparent_100%)]" />

              <div className="relative z-10 flex flex-col items-center gap-6">
                <div className="relative">
                  <div className="scan-orb flex h-24 w-24 items-center justify-center rounded-full border-2 border-[rgba(59,130,246,0.5)] border-t-[#3b82f6]">
                    <AppIcon className="h-12 w-12 text-[#3b82f6]" name="token" />
                  </div>
                  <div className="absolute -inset-4 rounded-full border border-[rgba(59,130,246,0.3)] opacity-20 animate-ping" />
                </div>

                <div className="space-y-2 text-center">
                  <h1 className="text-3xl font-extrabold tracking-tight text-white md:text-4xl">
                    Analyzing Token Risk...
                  </h1>
                  <p className="text-xs font-medium uppercase tracking-widest text-[#3b82f6]/70">
                    {labels[Math.min(phase, labels.length - 1)]} for {previewLabel}
                  </p>
                </div>
              </div>
            </div>

            <div className="mb-16 flex w-full max-w-xl flex-col gap-4">
              <div className="flex items-end justify-between">
                <span className="text-sm font-medium uppercase tracking-widest text-slate-400">Progress</span>
                <span className="text-2xl font-bold text-[#3b82f6]">{progressStops[phase]}%</span>
              </div>
              <div className="h-4 w-full overflow-hidden rounded-full border border-[rgba(59,130,246,0.1)] bg-slate-800 p-1">
                <div
                  className="scan-progress-glow h-full rounded-full bg-[#3b82f6] shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-[width] duration-700"
                  style={{ width: `${progressStops[phase]}%` }}
                />
              </div>
              <div className="mt-2 grid grid-cols-2 gap-4 md:grid-cols-4">
                <div className={`flex items-center gap-2 text-xs ${phase >= 1 ? "text-[#3b82f6]" : "text-slate-400"}`}>
                  <AppIcon className="h-4 w-4" name={phase >= 1 ? "check" : "token"} />
                  Rug-pull Check
                </div>
                <div className={`flex items-center gap-2 text-xs ${phase >= 2 ? "text-[#3b82f6]" : "text-slate-400"}`}>
                  <AppIcon className="h-4 w-4" name={phase >= 2 ? "check" : "drop"} />
                  Liquidity Scan
                </div>
                <div className={`flex items-center gap-2 text-xs ${phase >= 3 ? "text-[#3b82f6]" : "text-slate-400"}`}>
                  <AppIcon className={`h-4 w-4 ${phase === 3 ? "animate-spin" : ""}`} name={phase >= 4 ? "check" : "control"} />
                  Ownership Verification
                </div>
                <div className={`flex items-center gap-2 text-xs ${phase >= 4 ? "text-[#3b82f6]" : "text-slate-400"}`}>
                  <AppIcon className="h-4 w-4" name={phase >= 4 ? "check" : "hourglass"} />
                  Metadata Analysis
                </div>
              </div>
            </div>

            <div className="w-full">
              <div className="relative overflow-hidden rounded-2xl border border-[rgba(59,130,246,0.2)] bg-white p-8 dark:bg-slate-900/30 sm:flex sm:items-center sm:justify-between sm:gap-8">
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[#3b82f6]/10 blur-[100px]" />
                <div className="relative z-10 space-y-3">
                  <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Want the full report?</h3>
                  <p className="max-w-lg text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                    Register now to unlock <span className="font-semibold text-[#3b82f6]">10 free daily scans</span> and deep behavioral analysis from our AI security engine.
                  </p>
                </div>
                <div className="relative z-10 mt-8 shrink-0 sm:mt-0">
                  <Link
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#3b82f6] px-8 py-4 text-lg font-bold text-white shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all hover:bg-[#2563eb] sm:w-auto"
                    href="/register"
                  >
                    Sign Up Now
                    <AppIcon className="h-5 w-5" name="arrow-right" />
                  </Link>
                  <p className="mt-3 text-center text-xs text-slate-500 dark:text-slate-400">No credit card required</p>
                </div>
              </div>
            </div>

            {error ? (
              <section className="mt-8 w-full max-w-xl rounded-2xl border border-[rgba(248,113,113,0.25)] bg-[rgba(127,29,29,0.14)] p-5 text-center">
                <p className="text-sm text-rose-300">{error}</p>
                <div className="mt-4 flex justify-center gap-3">
                  <button
                    className="rounded-lg bg-[#3b82f6] px-5 py-3 text-sm font-bold text-white"
                    onClick={() => window.location.reload()}
                    type="button"
                  >
                    Retry analysis
                  </button>
                  <Link className="rounded-lg border border-[rgba(59,130,246,0.2)] px-5 py-3 text-sm font-semibold text-slate-200" href="/">
                    Back home
                  </Link>
                </div>
              </section>
            ) : null}
          </div>
        </main>
      </div>
    </main>
  );
}

function AnalysisPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const submittedValue = searchParams.get("value") ?? "";
  const submittedEntityType = (searchParams.get("entityType") as SubmitEntityType | null) ?? "token";
  const [phase, setPhase] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const previewLabel = useMemo(() => {
    const trimmed = submittedValue.trim();
    if (!trimmed) {
      return "LINK / Chainlink Token";
    }
    if (trimmed.length <= 22) {
      return trimmed;
    }
    return `${trimmed.slice(0, 10)}...${trimmed.slice(-6)}`;
  }, [submittedValue]);

  useEffect(() => {
    if (!submittedValue.trim()) {
      setError("Missing token address.");
      return;
    }

    let cancelled = false;
    const progressTimer = window.setInterval(() => {
      setPhase((current) => (current < 4 ? current + 1 : 4));
    }, 820);

    const run = async () => {
      try {
        const [result] = await Promise.all([
          submitCheck(submittedValue, submittedEntityType),
          wait(2900),
        ]);

        if (cancelled) {
          return;
        }

        router.replace(`/report/${result.entity_type}/${result.check_id}`);
        router.refresh();
      } catch (submitError) {
        if (cancelled) {
          return;
        }
        if (submitError instanceof ApiError) {
          setError(submitError.message);
        } else {
          setError("Unable to start analysis right now.");
        }
      } finally {
        window.clearInterval(progressTimer);
      }
    };

    void run();

    return () => {
      cancelled = true;
      window.clearInterval(progressTimer);
    };
  }, [router, submittedEntityType, submittedValue]);

  return <AnalysisLayout error={error} phase={phase} previewLabel={previewLabel} />;
}

export default function AnalysisPage() {
  return (
    <Suspense fallback={<AnalysisLayout error={null} phase={0} previewLabel="LINK / Chainlink Token" />}>
      <AnalysisPageContent />
    </Suspense>
  );
}
