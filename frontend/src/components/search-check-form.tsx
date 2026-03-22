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
  placeholder = "Paste a Solana token, wallet, or project URL",
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
  const selectorHidden = tokenOnly;

  const activePlaceholder =
    selectorHidden || entityType === "token"
      ? placeholder
      : entityType === "wallet"
        ? "Enter Solana wallet address"
        : "Enter project domain or URL";

  const onSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedValue = value.trim();
    if (!trimmedValue) {
      setError(
        entityType === "wallet"
          ? "Enter a Solana wallet address."
          : entityType === "project"
            ? "Enter a project domain or URL."
            : "Enter a token mint address.",
      );
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
            className="rounded-xl border border-[color:var(--border)] bg-[rgba(59,130,246,0.08)] px-4 py-4 pr-10 text-sm text-slate-100 outline-none appearance-none"
            onChange={(event) => setEntityType(event.target.value as SubmitEntityType)}
            style={{ colorScheme: "dark" }}
            value={entityType}
          >
            <option className="bg-[#081121] text-slate-100" value="token">Token</option>
            <option className="bg-[#081121] text-slate-100" value="wallet">Wallet</option>
            <option className="bg-[#081121] text-slate-100" value="project">Project</option>
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
          placeholder={activePlaceholder}
          type="text"
          value={value}
        />
        <button
          className={
            variant === "landing"
              ? "rounded-lg bg-[var(--accent)] px-8 font-bold text-white disabled:cursor-not-allowed disabled:opacity-70"
              : "rounded-xl bg-[var(--accent)] px-6 py-4 text-sm font-extrabold text-white disabled:cursor-not-allowed disabled:opacity-70"
          }
          disabled={isPending}
          type="submit"
        >
          {isPending ? "Checking..." : submitLabel}
        </button>
      </div>
      {error ? <p className="mt-3 text-sm text-[var(--critical)]">{error}</p> : null}
    </form>
  );
}
