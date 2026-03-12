"use client";

import { useRouter } from "next/navigation";
import { startTransition, useState } from "react";
import { AppIcon } from "@/components/app-icon";
import { ApiError, submitCheck, type SubmitEntityType } from "@/lib/api";

type SearchCheckFormProps = {
  defaultValue?: string;
  submitLabel?: string;
  placeholder?: string;
  tokenOnly?: boolean;
  leadingIcon?: boolean;
  variant?: "default" | "landing";
  submitMode?: "analysis" | "direct";
};

export function SearchCheckForm({
  defaultValue = "",
  submitLabel = "Check now",
  placeholder = "Paste a token mint address",
  tokenOnly = false,
  leadingIcon = false,
  variant = "default",
  submitMode = "analysis",
}: SearchCheckFormProps) {
  const router = useRouter();
  const [value, setValue] = useState(defaultValue);
  const [entityType, setEntityType] = useState<SubmitEntityType>("token");
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);
  const tokenOnlyMode = entityType !== "token";
  const selectorHidden = tokenOnly;

  const onSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedValue = value.trim();
    if (!trimmedValue) {
      setError("Enter a token mint address.");
      return;
    }

    if (tokenOnlyMode) {
      setError("Wallet and project checks are still in development. Token checks are live now.");
      return;
    }

    if (submitMode === "analysis") {
      const params = new URLSearchParams({
        value: trimmedValue,
        entityType,
      });
      router.push(`/analysis?${params.toString()}`);
      return;
    }

    setIsPending(true);
    setError(null);

    startTransition(async () => {
      try {
        const result = await submitCheck(trimmedValue, entityType);
        router.push(`/report/${result.entity_type}/${result.check_id}`);
        router.refresh();
      } catch (submitError) {
        if (submitError instanceof ApiError) {
          setError(submitError.message);
        } else {
          setError("Unable to create a report right now.");
        }
      } finally {
        setIsPending(false);
      }
    });
  };

  return (
    <form onSubmit={onSubmit}>
      <div
        className={
          variant === "landing"
            ? "flex w-full items-stretch rounded-xl border border-[rgba(59,130,246,0.2)] bg-[rgba(59,130,246,0.05)] p-1 backdrop-blur-sm"
            : "flex flex-col gap-3 rounded-[20px] border border-[color:var(--border)] bg-[rgba(15,23,42,0.74)] p-3 shadow-[0_18px_60px_rgba(2,6,23,0.28)] md:flex-row md:items-center"
        }
      >
        {selectorHidden ? null : (
          <select
            aria-label="Entity type"
            className="rounded-xl border border-[color:var(--border)] bg-[rgba(59,130,246,0.08)] px-4 py-4 text-sm outline-none"
            onChange={(event) => setEntityType(event.target.value as SubmitEntityType)}
            value={entityType}
          >
            <option value="token">Token</option>
            <option value="wallet">Wallet (In development)</option>
            <option value="project">Project (In development)</option>
          </select>
        )}
        {leadingIcon ? (
          <AppIcon
            className={
              variant === "landing"
                ? "mx-0 flex-shrink-0 self-center px-4 h-5 w-5 text-slate-400"
                : "mx-1 h-5 w-5 text-[var(--muted)] md:ml-2"
            }
            name="search"
          />
        ) : null}
        <input
          className={
            variant === "landing"
              ? "min-w-0 flex-1 border-none bg-transparent py-4 pr-4 text-sm text-slate-100 outline-none placeholder:text-slate-500"
              : "min-w-0 flex-1 rounded-xl border border-transparent bg-white/5 px-4 py-4 text-sm outline-none placeholder:text-[var(--muted)]"
          }
          onChange={(event) => setValue(event.target.value)}
          placeholder={placeholder}
          type="text"
          value={value}
        />
        <button
          className={
            variant === "landing"
              ? "rounded-lg bg-[var(--accent)] px-8 font-bold text-white disabled:cursor-not-allowed disabled:opacity-70"
              : "rounded-xl bg-[var(--accent)] px-6 py-4 text-sm font-extrabold text-white disabled:cursor-not-allowed disabled:opacity-70"
          }
          disabled={isPending || tokenOnlyMode}
          type="submit"
        >
          {tokenOnlyMode ? "In development" : isPending ? "Checking..." : submitLabel}
        </button>
      </div>
      {error ? <p className="mt-3 text-sm text-[var(--critical)]">{error}</p> : null}
    </form>
  );
}
