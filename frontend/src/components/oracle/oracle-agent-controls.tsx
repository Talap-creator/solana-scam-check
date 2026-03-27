"use client";

import { useState, useCallback } from "react";
import { startOracleAgent, stopOracleAgent } from "@/lib/api";

export function OracleAgentControls({ initialRunning }: { initialRunning: boolean }) {
  const [running, setRunning] = useState(initialRunning);
  const [loading, setLoading] = useState(false);

  const toggle = useCallback(async () => {
    setLoading(true);
    try {
      if (running) {
        await stopOracleAgent();
        setRunning(false);
      } else {
        await startOracleAgent();
        setRunning(true);
      }
    } catch {
      // silently fail, user can retry
    } finally {
      setLoading(false);
    }
  }, [running]);

  return (
    <button
      onClick={toggle}
      disabled={loading}
      className={`rounded-lg px-4 py-2 text-sm font-bold transition-all ${
        running
          ? "border border-rose-400/30 bg-rose-400/10 text-rose-300 hover:bg-rose-400/20"
          : "bg-[#2563eb] text-white shadow-[0_12px_24px_rgba(37,99,235,0.25)] hover:brightness-110"
      } disabled:opacity-50`}
    >
      {loading ? "..." : running ? "Stop Agent" : "Start Agent"}
    </button>
  );
}
