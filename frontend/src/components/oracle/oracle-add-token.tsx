"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { addOracleMonitor, getUsage, type UserUsage } from "@/lib/api";
import { PremiumCheckoutButton } from "@/components/premium-checkout-button";

export function OracleAddToken() {
  const [address, setAddress] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [usage, setUsage] = useState<UserUsage | null>(null);
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const data = await getUsage();
        if (!cancelled) setUsage(data);
      } catch {
        // ignore — usage banner handles errors
      }
    };
    void load();
    return () => { cancelled = true; };
  }, []);

  const exhausted = usage ? usage.remaining_today <= 0 : false;
  const isFree = usage?.plan === "free";

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!address.trim()) return;

      if (exhausted && isFree) {
        setError("Daily limit reached. Upgrade to Pro for 200 operations/day.");
        return;
      }

      setLoading(true);
      setError("");
      setSuccess("");

      try {
        await addOracleMonitor(address.trim(), name.trim() || undefined);
        setSuccess(`Added ${address.slice(0, 8)}... to monitoring`);
        setAddress("");
        setName("");
        // Refresh usage after operation
        try {
          const updated = await getUsage();
          setUsage(updated);
        } catch { /* ignore */ }
        router.refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to add token");
      } finally {
        setLoading(false);
      }
    },
    [address, name, router, exhausted, isFree]
  );

  return (
    <article className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-4 sm:p-6">
      <h2 className="mb-1 text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">
        Add Token to Monitor
      </h2>
      <p className="mb-4 text-xs text-slate-400">
        AI agent will score this token and publish the result on-chain
      </p>

      {usage && isFree && (
        <div className={`mb-4 rounded-lg px-3 py-2 text-xs ${
          exhausted
            ? "border border-rose-400/30 bg-rose-400/10 text-rose-300"
            : "border border-[rgba(59,130,246,0.2)] bg-[rgba(59,130,246,0.06)] text-slate-400"
        }`}>
          {exhausted
            ? "Daily limit reached — upgrade to continue"
            : `${usage.remaining_today} of ${usage.daily_limit} free operations remaining today`
          }
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Token mint address (e.g. EPjFWdd5...)"
          className="w-full rounded-lg border border-[rgba(59,130,246,0.2)] bg-[rgba(2,6,23,0.6)] px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition-colors focus:border-[#3b82f6]/50"
        />
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Display name (optional)"
          className="w-full rounded-lg border border-[rgba(59,130,246,0.2)] bg-[rgba(2,6,23,0.6)] px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition-colors focus:border-[#3b82f6]/50"
        />

        {exhausted && isFree ? (
          <PremiumCheckoutButton
            className="w-full rounded-lg bg-[linear-gradient(135deg,#2563eb,#38bdf8)] px-4 py-2.5 text-sm font-bold text-white"
            label="Upgrade to Pro"
          />
        ) : (
          <button
            type="submit"
            disabled={loading || !address.trim()}
            className="w-full rounded-lg bg-[#2563eb] px-4 py-2.5 text-sm font-bold text-white shadow-[0_12px_24px_rgba(37,99,235,0.25)] transition-all hover:brightness-110 disabled:opacity-50"
          >
            {loading ? "Adding..." : "Add to Oracle Monitor"}
          </button>
        )}
      </form>

      {error && (
        <p className="mt-3 text-xs text-rose-400">{error}</p>
      )}
      {success && (
        <p className="mt-3 text-xs text-emerald-400">{success}</p>
      )}
    </article>
  );
}
