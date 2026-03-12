"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  bulkUpdateAdminUserLimits,
  getAdminDashboard,
  getAdminOverrides,
  getAdminScans,
  getAdminTokens,
  getAdminUsers,
  getMe,
  getReviewQueue,
  updateAdminUserLimits,
  upsertAdminOverride,
  deleteAdminOverride,
  type AdminDashboardData,
  type AdminTokenOverrideItem,
  type AdminScanItem,
  type AdminTokenItem,
  type AdminUserItem,
  type ReviewQueueItem,
  type TokenOverrideVerdict,
} from "@/lib/api";
import { SearchCheckForm } from "@/components/search-check-form";
import { formatPlanLabel } from "@/lib/plans";

type AdminState = {
  dashboard: AdminDashboardData | null;
  users: AdminUserItem[];
  scans: AdminScanItem[];
  tokens: AdminTokenItem[];
  overrides: AdminTokenOverrideItem[];
  queue: ReviewQueueItem[];
};

type UserLimitDraft = {
  plan: "free" | "pro" | "enterprise";
  customDailyScanLimit: string;
};

type AuthMode = "checking" | "unauth" | "forbidden" | "ok";

const pageShellClass =
  "min-h-screen bg-[radial-gradient(circle_at_top,rgba(73,140,255,0.16),transparent_32%),var(--background)] text-[var(--foreground)]";
const panelClass =
  "rounded-[28px] border border-[color:rgba(148,163,184,0.2)] bg-[linear-gradient(180deg,rgba(15,23,42,0.9),rgba(15,23,42,0.78))] shadow-[0_24px_80px_rgba(2,6,23,0.28)]";
const softPanelClass =
  "rounded-[24px] border border-[color:rgba(148,163,184,0.16)] bg-[rgba(15,23,42,0.72)] shadow-[0_16px_48px_rgba(2,6,23,0.16)]";
const fieldClass =
  "rounded-2xl border border-[color:rgba(148,163,184,0.16)] bg-[rgba(148,163,184,0.08)] px-3 py-2 text-sm text-[var(--foreground)] outline-none transition focus:border-[rgba(96,165,250,0.45)] focus:bg-[rgba(30,41,59,0.9)]";
const secondaryButtonClass =
  "rounded-full border border-[color:rgba(148,163,184,0.18)] bg-[rgba(148,163,184,0.08)] px-4 py-2 text-sm font-semibold text-[var(--foreground)] transition hover:border-[rgba(96,165,250,0.35)] hover:bg-[rgba(30,41,59,0.92)]";
const primaryButtonClass =
  "rounded-full bg-[linear-gradient(135deg,#60a5fa,#93c5fd)] px-4 py-2 text-sm font-bold text-slate-950 shadow-[0_12px_32px_rgba(96,165,250,0.25)] transition hover:brightness-105 disabled:opacity-60";
const tableClass = "w-full min-w-[980px] text-left text-sm";
const rowClass = "border-t border-[color:rgba(148,163,184,0.12)]";
const emptyTableCellClass = "px-3 py-4 text-[var(--muted)]";

function planBadgeClass(plan: string): string {
  if (plan === "pro") {
    return "border-[rgba(59,130,246,0.28)] bg-[rgba(59,130,246,0.12)] text-[#93c5fd]";
  }
  if (plan === "enterprise") {
    return "border-[rgba(45,212,191,0.28)] bg-[rgba(45,212,191,0.12)] text-[#99f6e4]";
  }
  return "border-[rgba(148,163,184,0.22)] bg-[rgba(148,163,184,0.08)] text-slate-300";
}

export default function AdminPage() {
  const [authMode, setAuthMode] = useState<AuthMode>("checking");
  const [state, setState] = useState<AdminState>({
    dashboard: null,
    users: [],
    scans: [],
    tokens: [],
    overrides: [],
    queue: [],
  });
  const [userDrafts, setUserDrafts] = useState<Record<string, UserLimitDraft>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overrideAddress, setOverrideAddress] = useState("");
  const [overrideVerdict, setOverrideVerdict] = useState<TokenOverrideVerdict>("whitelist");
  const [overrideReason, setOverrideReason] = useState("");
  const [overridePending, setOverridePending] = useState(false);
  const [userLimitPendingId, setUserLimitPendingId] = useState<string | null>(null);
  const [selectedUsers, setSelectedUsers] = useState<Record<string, boolean>>({});
  const [userFilterQuery, setUserFilterQuery] = useState("");
  const [userFilterPlan, setUserFilterPlan] = useState<"all" | "free" | "pro" | "enterprise">("all");
  const [bulkPlan, setBulkPlan] = useState<"free" | "pro" | "enterprise">("free");
  const [bulkCustomLimit, setBulkCustomLimit] = useState("");
  const [bulkPending, setBulkPending] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const me = await getMe();
        if (cancelled) {
          return;
        }
        if (me.role !== "admin") {
          setAuthMode("forbidden");
          setIsLoading(false);
          return;
        }

        setAuthMode("ok");
        const [dashboard, users, scans, tokens, overrides, queue] = await Promise.allSettled([
          getAdminDashboard(),
          getAdminUsers(),
          getAdminScans(),
          getAdminTokens(),
          getAdminOverrides(),
          getReviewQueue(),
        ]);

        if (cancelled) {
          return;
        }

        const failedSections: string[] = [];
        const nextState: AdminState = {
          dashboard:
            dashboard.status === "fulfilled"
              ? dashboard.value
              : (failedSections.push("dashboard"), null),
          users: users.status === "fulfilled" ? users.value : (failedSections.push("users"), []),
          scans: scans.status === "fulfilled" ? scans.value : (failedSections.push("scans"), []),
          tokens: tokens.status === "fulfilled" ? tokens.value : (failedSections.push("tokens"), []),
          overrides:
            overrides.status === "fulfilled"
              ? overrides.value
              : (failedSections.push("overrides"), []),
          queue: queue.status === "fulfilled" ? queue.value : (failedSections.push("review queue"), []),
        };

        setState(nextState);
        setUserDrafts(
          Object.fromEntries(
            nextState.users.map((user) => [
              user.id,
              {
                plan: user.plan as "free" | "pro" | "enterprise",
                customDailyScanLimit:
                  user.custom_daily_scan_limit !== null ? String(user.custom_daily_scan_limit) : "",
              },
            ]),
          ),
        );
        setSelectedUsers({});
        setError(
          failedSections.length > 0
            ? `Some admin sections failed to load: ${failedSections.join(", ")}.`
            : null,
        );
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        if (loadError instanceof ApiError && loadError.status === 401) {
          setAuthMode("unauth");
        } else if (loadError instanceof ApiError && loadError.status === 403) {
          setAuthMode("forbidden");
        } else {
          setAuthMode("ok");
          setError(loadError instanceof ApiError ? loadError.message : "Unable to load admin data right now.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const onCreateOverride = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setOverridePending(true);
    setError(null);
    try {
      const created = await upsertAdminOverride(overrideAddress, overrideVerdict, overrideReason);
      setState((prev) => {
        const without = prev.overrides.filter((item) => item.token_address !== created.token_address);
        return { ...prev, overrides: [created, ...without] };
      });
      setOverrideAddress("");
      setOverrideReason("");
    } catch (submitError) {
      setError(submitError instanceof ApiError ? submitError.message : "Unable to save override.");
    } finally {
      setOverridePending(false);
    }
  };

  const onDeleteOverride = async (tokenAddress: string) => {
    setOverridePending(true);
    setError(null);
    try {
      await deleteAdminOverride(tokenAddress);
      setState((prev) => ({
        ...prev,
        overrides: prev.overrides.filter((item) => item.token_address !== tokenAddress),
      }));
    } catch (deleteError) {
      setError(deleteError instanceof ApiError ? deleteError.message : "Unable to delete override.");
    } finally {
      setOverridePending(false);
    }
  };

  const onSaveUserLimit = async (user: AdminUserItem) => {
    const draft = userDrafts[user.id];
    if (!draft) {
      return;
    }

    const custom =
      draft.customDailyScanLimit.trim() === "" ? null : Number.parseInt(draft.customDailyScanLimit, 10);
    if (custom !== null && (Number.isNaN(custom) || custom < 1)) {
      setError("Custom limit must be a positive number.");
      return;
    }

    setError(null);
    setUserLimitPendingId(user.id);
    try {
      const updated = await updateAdminUserLimits(user.id, draft.plan, custom);
      setState((prev) => ({
        ...prev,
        users: prev.users.map((row) => (row.id === updated.id ? updated : row)),
      }));
      setUserDrafts((prev) => ({
        ...prev,
        [updated.id]: {
          plan: updated.plan as "free" | "pro" | "enterprise",
          customDailyScanLimit:
            updated.custom_daily_scan_limit !== null ? String(updated.custom_daily_scan_limit) : "",
        },
      }));
    } catch (updateError) {
      setError(updateError instanceof ApiError ? updateError.message : "Unable to update user limits.");
    } finally {
      setUserLimitPendingId(null);
    }
  };

  const filteredUsers = state.users.filter((user) => {
    const byQuery =
      userFilterQuery.trim() === "" ||
      user.email.toLowerCase().includes(userFilterQuery.trim().toLowerCase());
    const byPlan = userFilterPlan === "all" || user.plan === userFilterPlan;
    return byQuery && byPlan;
  });

  const selectedFilteredIds = filteredUsers.filter((user) => selectedUsers[user.id]).map((user) => user.id);
  const allFilteredSelected = filteredUsers.length > 0 && selectedFilteredIds.length === filteredUsers.length;
  const planDistribution = useMemo(() => {
    return state.users.reduce(
      (acc, user) => {
        if (user.plan === "pro") {
          acc.pro += 1;
        } else if (user.plan === "enterprise") {
          acc.enterprise += 1;
        } else {
          acc.free += 1;
        }
        return acc;
      },
      { enterprise: 0, free: 0, pro: 0 },
    );
  }, [state.users]);

  const toggleSelectAllFiltered = () => {
    setSelectedUsers((prev) => {
      const next = { ...prev };
      if (allFilteredSelected) {
        for (const user of filteredUsers) {
          delete next[user.id];
        }
      } else {
        for (const user of filteredUsers) {
          next[user.id] = true;
        }
      }
      return next;
    });
  };

  const onApplyBulkLimits = async () => {
    if (selectedFilteredIds.length === 0) {
      setError("Select at least one user for bulk update.");
      return;
    }
    const custom =
      bulkCustomLimit.trim() === "" ? null : Number.parseInt(bulkCustomLimit.trim(), 10);
    if (custom !== null && (Number.isNaN(custom) || custom < 1)) {
      setError("Bulk custom limit must be a positive number.");
      return;
    }

    setBulkPending(true);
    setError(null);
    try {
      await bulkUpdateAdminUserLimits(selectedFilteredIds, bulkPlan, custom);
      setState((prev) => ({
        ...prev,
        users: prev.users.map((user) =>
          selectedFilteredIds.includes(user.id)
            ? {
                ...user,
                plan: bulkPlan,
                custom_daily_scan_limit: custom,
                effective_daily_limit:
                  custom !== null ? custom : bulkPlan === "pro" ? 200 : bulkPlan === "enterprise" ? 1000 : 5,
              }
            : user,
        ),
      }));
      setUserDrafts((prev) => {
        const next = { ...prev };
        for (const id of selectedFilteredIds) {
          next[id] = {
            plan: bulkPlan,
            customDailyScanLimit: custom !== null ? String(custom) : "",
          };
        }
        return next;
      });
    } catch (bulkError) {
      setError(bulkError instanceof ApiError ? bulkError.message : "Unable to apply bulk limits.");
    } finally {
      setBulkPending(false);
    }
  };

  if (authMode === "checking" || (authMode === "ok" && isLoading)) {
    return (
      <main className={`grid place-items-center px-4 ${pageShellClass}`}>
        <div className={`${panelClass} w-full max-w-md px-6 py-10 text-center`}>
          <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[var(--accent)]">Admin</p>
          <p className="mt-4 text-sm text-[var(--muted)]">Checking admin access...</p>
        </div>
      </main>
    );
  }

  if (authMode === "unauth") {
    return (
      <main className={`grid place-items-center px-4 ${pageShellClass}`}>
        <section className={`${panelClass} w-full max-w-lg p-8 text-center`}>
          <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[var(--accent)]">Restricted</p>
          <h1 className="mt-3 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.04em]">
            Admin login required
          </h1>
          <p className="mt-3 text-sm text-[var(--muted)]">
            Login with an account that has admin role.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-2">
            <Link className={primaryButtonClass} href="/login">
              Login
            </Link>
            <Link className={secondaryButtonClass} href="/dashboard">
              Go dashboard
            </Link>
          </div>
        </section>
      </main>
    );
  }

  if (authMode === "forbidden") {
    return (
      <main className={`grid place-items-center px-4 ${pageShellClass}`}>
        <section className={`${panelClass} w-full max-w-lg p-8 text-center`}>
          <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[var(--accent)]">Restricted</p>
          <h1 className="mt-3 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.04em]">
            Access denied
          </h1>
          <p className="mt-3 text-sm text-[var(--muted)]">
            Your account is logged in, but it does not have admin permissions.
          </p>
          <div className="mt-5">
            <Link className={secondaryButtonClass} href="/dashboard">
              Go dashboard
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className={pageShellClass}>
      <div className="mx-auto w-full max-w-[1280px] px-5 py-6 md:px-8 md:py-8">
        <header className={`${panelClass} mb-7 flex flex-col gap-6 px-6 py-6 md:flex-row md:items-end md:justify-between`}>
          <div className="max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[var(--accent)]">Admin console</p>
            <h1 className="mt-2 font-[family:var(--font-display)] text-4xl font-bold tracking-[-0.05em] md:text-5xl">
              Platform control panel
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-[var(--muted)]">
              Moderate tokens, manage user limits, inspect scan throughput, and apply token verdict overrides from one control surface.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className={`${softPanelClass} px-4 py-3`}>
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--accent)]">Mode</p>
              <p className="mt-1 text-sm text-[var(--muted)]">Live admin moderation</p>
            </div>
            <Link className={secondaryButtonClass} href="/dashboard">
              Back to dashboard
            </Link>
          </div>
        </header>
        <section className="mb-6 grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
          <article className={`${panelClass} p-5`}>
            <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[var(--accent)]">Admin checker</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">Run token check with admin context</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Dedicated checker for moderation flow. Run a scan, review the report, then apply overrides below if needed.
            </p>
            <div className="mt-4">
              <SearchCheckForm
                placeholder="Paste token mint for moderation review"
                submitLabel="Run admin check"
                submitMode="direct"
              />
            </div>
          </article>
          <article className={`${panelClass} grid gap-3 p-5`}>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[var(--accent)]">Operational notes</p>
              <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em]">Admin workflow</h2>
            </div>
            <div className="grid gap-3">
              <div className={`${softPanelClass} p-4`}>
                <p className="text-sm font-medium">1. Scan suspicious token</p>
                <p className="mt-1 text-sm text-[var(--muted)]">Run a moderation scan with the checker above.</p>
              </div>
              <div className={`${softPanelClass} p-4`}>
                <p className="text-sm font-medium">2. Review user and feed impact</p>
                <p className="mt-1 text-sm text-[var(--muted)]">Inspect scans, user activity, and recent overrides.</p>
              </div>
              <div className={`${softPanelClass} p-4`}>
                <p className="text-sm font-medium">3. Apply override or limit changes</p>
                <p className="mt-1 text-sm text-[var(--muted)]">Use overrides and limit controls only after review.</p>
              </div>
            </div>
          </article>
        </section>

        {error ? (
          <section className="mb-6 rounded-[24px] border border-[color:rgba(248,113,113,0.35)] bg-[rgba(127,29,29,0.18)] p-4">
            <p className="text-sm text-[var(--critical)]">{error}</p>
          </section>
        ) : null}

        {state.dashboard ? (
          <section className="grid gap-4 md:grid-cols-4">
            <article className={`${softPanelClass} p-4`}>
              <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--muted)]">Users</span>
              <strong className="mt-3 block text-3xl">{state.dashboard.users_count}</strong>
            </article>
            <article className={`${softPanelClass} p-4`}>
              <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--muted)]">Daily scans</span>
              <strong className="mt-3 block text-3xl">{state.dashboard.daily_scans}</strong>
            </article>
            <article className={`${softPanelClass} p-4`}>
              <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--muted)]">Average risk</span>
              <strong className="mt-3 block text-3xl">{state.dashboard.average_risk_score}</strong>
            </article>
            <article className={`${softPanelClass} p-4`}>
              <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--muted)]">Popular tokens</span>
              <strong className="mt-3 block text-3xl">{state.dashboard.popular_tokens.length}</strong>
            </article>
          </section>
        ) : (
          <section className={`${softPanelClass} p-4 text-sm text-[var(--muted)]`}>
            Dashboard metrics are unavailable right now, but the admin tools below still work.
          </section>
        )}

        <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[
            ["Freemium accounts", String(planDistribution.free), "Free-tier monitoring"],
            ["Premium accounts", String(planDistribution.pro), "Paid daily workflows"],
            ["Enterprise accounts", String(planDistribution.enterprise), "Manual onboarding"],
            ["Control surface", `${state.scans.length}/${state.tokens.length}/${state.overrides.length}`, "Scans / Tokens / Overrides"],
          ].map(([label, value, detail]) => (
            <article key={label} className={`${softPanelClass} p-4`}>
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--muted)]">{label}</p>
              <strong className="mt-3 block text-3xl">{value}</strong>
              <p className="mt-2 text-sm text-[var(--muted)]">{detail}</p>
            </article>
          ))}
        </section>

        <section className="mt-6 grid gap-6">
          <article className={`${panelClass} p-5`}>
            <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[var(--accent)]">Accounts</p>
                <h2 className="mt-1 text-xl font-semibold tracking-[-0.03em]">Users and limits</h2>
              </div>
              <p className="text-sm text-[var(--muted)]">
                {filteredUsers.length} user{filteredUsers.length === 1 ? "" : "s"} in current view.
              </p>
            </div>
            <div className="mt-3 grid gap-3 md:grid-cols-[1.2fr_0.8fr_auto]">
              <input
                className={fieldClass}
                onChange={(event) => setUserFilterQuery(event.target.value)}
                placeholder="Filter by email"
                value={userFilterQuery}
              />
              <select
                className={fieldClass}
                onChange={(event) =>
                  setUserFilterPlan(event.target.value as "all" | "free" | "pro" | "enterprise")
                }
                value={userFilterPlan}
              >
                <option value="all">all plans</option>
                <option value="free">freemium</option>
                <option value="pro">premium</option>
                <option value="enterprise">enterprise</option>
              </select>
              <button
                className={secondaryButtonClass}
                onClick={toggleSelectAllFiltered}
                type="button"
              >
                {allFilteredSelected ? "Unselect filtered" : "Select filtered"}
              </button>
            </div>

            <div className="mt-3 grid gap-3 rounded-[22px] border border-[color:rgba(148,163,184,0.16)] bg-[rgba(148,163,184,0.08)] p-3 md:grid-cols-[0.8fr_0.8fr_auto_auto] md:items-center">
              <select
                className={fieldClass}
                onChange={(event) => setBulkPlan(event.target.value as "free" | "pro" | "enterprise")}
                value={bulkPlan}
              >
                <option value="free">bulk plan: freemium</option>
                <option value="pro">bulk plan: premium</option>
                <option value="enterprise">bulk plan: enterprise</option>
              </select>
              <input
                className={fieldClass}
                onChange={(event) => setBulkCustomLimit(event.target.value)}
                placeholder="bulk custom/day (optional)"
                type="number"
                value={bulkCustomLimit}
              />
              <span className="text-sm text-[var(--muted)]">
                Selected: {selectedFilteredIds.length}
              </span>
              <button
                className={primaryButtonClass}
                disabled={bulkPending}
                onClick={() => void onApplyBulkLimits()}
                type="button"
              >
                {bulkPending ? "Applying..." : "Apply bulk limits"}
              </button>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              {[
                ["Freemium", String(planDistribution.free), "5 requests/day"],
                ["Premium", String(planDistribution.pro), "200 requests/day"],
                ["Enterprise", String(planDistribution.enterprise), "Custom request caps"],
              ].map(([label, value, detail]) => (
                <div
                  key={label}
                  className="rounded-[20px] border border-[color:rgba(148,163,184,0.14)] bg-[rgba(148,163,184,0.06)] px-4 py-4"
                >
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">{label}</p>
                  <strong className="mt-2 block text-2xl text-[var(--foreground)]">{value}</strong>
                  <p className="mt-1 text-sm text-[var(--muted)]">{detail}</p>
                </div>
              ))}
            </div>
            <div className="mt-4 overflow-x-auto rounded-[22px] border border-[color:rgba(148,163,184,0.14)]">
              <table className="w-full min-w-[1080px] text-left text-sm">
                <thead>
                  <tr className="bg-[rgba(15,23,42,0.92)] text-[11px] uppercase tracking-[0.18em] text-[var(--muted)]">
                    <th className="px-3 py-3">Select</th>
                    <th className="px-3 py-3">Email</th>
                    <th className="px-3 py-3">Plan</th>
                    <th className="px-3 py-3">Custom/day</th>
                    <th className="px-3 py-3">Effective/day</th>
                    <th className="px-3 py-3">Scans</th>
                    <th className="px-3 py-3">Created</th>
                    <th className="px-3 py-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.length === 0 ? (
                    <tr className={rowClass}>
                      <td className={emptyTableCellClass} colSpan={8}>
                        No users match the current filters.
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((item) => {
                      const draft = userDrafts[item.id];
                      return (
                        <tr key={item.id} className={rowClass}>
                          <td className="px-3 py-3">
                            <input
                              checked={Boolean(selectedUsers[item.id])}
                              onChange={(event) =>
                                setSelectedUsers((prev) => ({
                                  ...prev,
                                  [item.id]: event.target.checked,
                                }))
                              }
                              type="checkbox"
                            />
                        </td>
                        <td className="px-3 py-3">{item.email}</td>
                        <td className="px-3 py-3">
                          <div className="flex flex-col gap-2">
                            <span
                              className={`inline-flex w-fit rounded-full border px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] ${planBadgeClass(draft?.plan ?? item.plan)}`}
                            >
                              {formatPlanLabel(draft?.plan ?? item.plan)}
                            </span>
                            <select
                              className="rounded-xl border border-[color:rgba(148,163,184,0.16)] bg-[rgba(148,163,184,0.08)] px-2 py-1"
                              onChange={(event) =>
                                setUserDrafts((prev) => ({
                                  ...prev,
                                  [item.id]: {
                                    ...(prev[item.id] ?? { plan: "free", customDailyScanLimit: "" }),
                                    plan: event.target.value as "free" | "pro" | "enterprise",
                                  },
                                }))
                              }
                              value={draft?.plan ?? item.plan}
                            >
                              <option value="free">{formatPlanLabel("free")}</option>
                              <option value="pro">{formatPlanLabel("pro")}</option>
                              <option value="enterprise">{formatPlanLabel("enterprise")}</option>
                            </select>
                          </div>
                        </td>
                          <td className="px-3 py-3">
                            <input
                              className="w-28 rounded-xl border border-[color:rgba(148,163,184,0.16)] bg-[rgba(148,163,184,0.08)] px-2 py-1"
                              onChange={(event) =>
                                setUserDrafts((prev) => ({
                                  ...prev,
                                  [item.id]: {
                                    ...(prev[item.id] ?? { plan: "free", customDailyScanLimit: "" }),
                                    customDailyScanLimit: event.target.value,
                                  },
                                }))
                              }
                              placeholder="default"
                              type="number"
                              value={draft?.customDailyScanLimit ?? ""}
                            />
                          </td>
                          <td className="px-3 py-3">{item.effective_daily_limit}</td>
                          <td className="px-3 py-3">{item.scans}</td>
                          <td className="px-3 py-3">{new Date(item.created_at).toLocaleString()}</td>
                          <td className="px-3 py-3">
                            <button
                              className={secondaryButtonClass}
                              disabled={userLimitPendingId === item.id}
                              onClick={() => void onSaveUserLimit(item)}
                              type="button"
                            >
                              {userLimitPendingId === item.id ? "Saving..." : "Save"}
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </article>

          <article className={`${panelClass} p-5`}>
            <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[var(--accent)]">Telemetry</p>
                <h2 className="mt-1 text-xl font-semibold tracking-[-0.03em]">What users tested</h2>
              </div>
              <p className="text-sm text-[var(--muted)]">
                {state.scans.length} recent scan event{state.scans.length === 1 ? "" : "s"}.
              </p>
            </div>
            <div className="mt-4 overflow-x-auto rounded-[22px] border border-[color:rgba(148,163,184,0.14)]">
              <table className={tableClass}>
                <thead>
                  <tr className="bg-[rgba(15,23,42,0.92)] text-[11px] uppercase tracking-[0.18em] text-[var(--muted)]">
                    <th className="px-3 py-3">User</th>
                    <th className="px-3 py-3">Token</th>
                    <th className="px-3 py-3">Risk</th>
                    <th className="px-3 py-3">Confidence</th>
                    <th className="px-3 py-3">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {state.scans.length === 0 ? (
                    <tr className={rowClass}>
                      <td className={emptyTableCellClass} colSpan={5}>
                        No user scan activity is available yet.
                      </td>
                    </tr>
                  ) : (
                    state.scans.map((item) => (
                      <tr key={item.id} className={rowClass}>
                        <td className="px-3 py-3">{item.user_email}</td>
                        <td className="px-3 py-3">{item.token_address}</td>
                        <td className="px-3 py-3">{item.risk_score}</td>
                        <td className="px-3 py-3">{item.confidence.toFixed(2)}</td>
                        <td className="px-3 py-3">{new Date(item.scan_time).toLocaleString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </article>

          <article className={`${panelClass} p-5`}>
            <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[var(--accent)]">Coverage</p>
                <h2 className="mt-1 text-xl font-semibold tracking-[-0.03em]">Tokens</h2>
              </div>
              <p className="text-sm text-[var(--muted)]">Frequently scanned assets and last activity.</p>
            </div>
            <div className="mt-4 overflow-x-auto rounded-[22px] border border-[color:rgba(148,163,184,0.14)]">
              <table className="w-full min-w-[900px] text-left text-sm">
                <thead>
                  <tr className="bg-[rgba(15,23,42,0.92)] text-[11px] uppercase tracking-[0.18em] text-[var(--muted)]">
                    <th className="px-3 py-3">Token</th>
                    <th className="px-3 py-3">Scan count</th>
                    <th className="px-3 py-3">Average risk</th>
                    <th className="px-3 py-3">Last scanned</th>
                  </tr>
                </thead>
                <tbody>
                  {state.tokens.length === 0 ? (
                    <tr className={rowClass}>
                      <td className={emptyTableCellClass} colSpan={4}>
                        No token activity has been recorded yet.
                      </td>
                    </tr>
                  ) : (
                    state.tokens.map((item) => (
                      <tr key={item.token_address} className={rowClass}>
                        <td className="px-3 py-3">{item.token_address}</td>
                        <td className="px-3 py-3">{item.scan_count}</td>
                        <td className="px-3 py-3">{item.average_risk_score}</td>
                        <td className="px-3 py-3">{new Date(item.last_scanned).toLocaleString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </article>

          <article className={`${panelClass} p-5`}>
            <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[var(--accent)]">Moderation</p>
                <h2 className="mt-1 text-xl font-semibold tracking-[-0.03em]">Overrides</h2>
              </div>
              <p className="text-sm text-[var(--muted)]">Whitelist or blacklist specific tokens with an audit note.</p>
            </div>
            <form className="mt-3 grid gap-3 md:grid-cols-[1.5fr_0.8fr_1.2fr_auto]" onSubmit={onCreateOverride}>
              <input
                className={fieldClass}
                onChange={(event) => setOverrideAddress(event.target.value)}
                placeholder="Token address"
                required
                value={overrideAddress}
              />
              <select
                className={fieldClass}
                onChange={(event) => setOverrideVerdict(event.target.value as TokenOverrideVerdict)}
                value={overrideVerdict}
              >
                <option value="whitelist">whitelist</option>
                <option value="blacklist">blacklist</option>
              </select>
              <input
                className={fieldClass}
                onChange={(event) => setOverrideReason(event.target.value)}
                placeholder="Reason (optional)"
                value={overrideReason}
              />
              <button
                className={primaryButtonClass}
                disabled={overridePending}
                type="submit"
              >
                Save
              </button>
            </form>
            <div className="mt-4 overflow-x-auto rounded-[22px] border border-[color:rgba(148,163,184,0.14)]">
              <table className={tableClass}>
                <thead>
                  <tr className="bg-[rgba(15,23,42,0.92)] text-[11px] uppercase tracking-[0.18em] text-[var(--muted)]">
                    <th className="px-3 py-3">Token</th>
                    <th className="px-3 py-3">Verdict</th>
                    <th className="px-3 py-3">Reason</th>
                    <th className="px-3 py-3">Updated</th>
                    <th className="px-3 py-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {state.overrides.length === 0 ? (
                    <tr className={rowClass}>
                      <td className={emptyTableCellClass} colSpan={5}>
                        No moderator overrides have been created yet.
                      </td>
                    </tr>
                  ) : (
                    state.overrides.map((item) => (
                      <tr key={item.token_address} className={rowClass}>
                        <td className="px-3 py-3">{item.token_address}</td>
                        <td className="px-3 py-3">{item.verdict}</td>
                        <td className="px-3 py-3">{item.reason ?? "-"}</td>
                        <td className="px-3 py-3">{new Date(item.updated_at).toLocaleString()}</td>
                        <td className="px-3 py-3">
                          <button
                            className={secondaryButtonClass}
                            disabled={overridePending}
                            onClick={() => void onDeleteOverride(item.token_address)}
                            type="button"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </article>

          <article className={`${panelClass} p-5`}>
            <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[var(--accent)]">Review queue</p>
                <h2 className="mt-1 text-xl font-semibold tracking-[-0.03em]">Manual moderation candidates</h2>
              </div>
              <p className="text-sm text-[var(--muted)]">Latest assets pushed into the moderation queue.</p>
            </div>
            <div className="mt-4 overflow-x-auto rounded-[22px] border border-[color:rgba(148,163,184,0.14)]">
              <table className={tableClass}>
                <thead>
                  <tr className="bg-[rgba(15,23,42,0.92)] text-[11px] uppercase tracking-[0.18em] text-[var(--muted)]">
                    <th className="px-3 py-3">Token</th>
                    <th className="px-3 py-3">Reason</th>
                    <th className="px-3 py-3">Queued</th>
                  </tr>
                </thead>
                <tbody>
                  {state.queue.length === 0 ? (
                    <tr className={rowClass}>
                      <td className="px-3 py-4 text-[var(--muted)]" colSpan={3}>
                        Queue is empty.
                      </td>
                    </tr>
                  ) : (
                    state.queue.map((item) => (
                      <tr key={item.id} className={rowClass}>
                        <td className="px-3 py-3">{item.display_name}</td>
                        <td className="px-3 py-3">{`${item.entity_type} | ${item.owner} | ${item.severity}`}</td>
                        <td className="px-3 py-3">{new Date(item.updated_at).toLocaleString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </article>
        </section>
      </div>
    </main>
  );
}
