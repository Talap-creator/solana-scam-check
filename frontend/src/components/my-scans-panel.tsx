"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, getMyScans, type UserScan } from "@/lib/api";

export function MyScansPanel() {
  const [scans, setScans] = useState<UserScan[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getMyScans();
        if (!cancelled) {
          setScans(data.slice(0, 8));
        }
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        if (loadError instanceof ApiError && loadError.status === 401) {
          setError("Login to see your personal scan history.");
        } else {
          setError("Unable to load personal scans right now.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="mt-6 rounded-[24px] border border-[color:var(--border)] bg-[var(--panel)] p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-bold">My scans</h3>
        <Link className="text-sm font-semibold text-[var(--accent)]" href="/history">
          Open history
        </Link>
      </div>

      {loading ? <p className="mt-3 text-sm text-[var(--muted)]">Loading...</p> : null}
      {error ? <p className="mt-3 text-sm text-[var(--muted)]">{error}</p> : null}

      {!loading && !error ? (
        scans.length > 0 ? (
          <div className="mt-3 grid gap-2">
            {scans.map((item) => (
              <article
                key={item.id}
                className="rounded-2xl border border-[color:var(--border)] bg-white/6 px-3 py-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <strong className="truncate text-sm">{item.token_address}</strong>
                  <span className="text-xs text-[var(--muted)]">
                    {new Date(item.scan_time).toLocaleString()}
                  </span>
                </div>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  Risk {item.risk_score} | Confidence {item.confidence.toFixed(2)}
                </p>
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-[var(--muted)]">No scans yet.</p>
        )
      ) : null}
    </section>
  );
}
