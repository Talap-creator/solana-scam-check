"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { AppIcon } from "@/components/app-icon";
import type { LaunchFeedItem } from "@/lib/api";
import {
  copycatLabel,
  copycatTone,
  formatAge,
  formatMoney,
  formatUpdated,
  launchTone,
  summaryFallback,
  tradeCautionLabel,
} from "./utils";

type CoinsFeedRowProps = {
  item: LaunchFeedItem;
  expanded: boolean;
  onToggle: () => void;
};

function riskBadgeClass(level: LaunchFeedItem["rug_risk_level"]) {
  if (level === "critical") return "border border-rose-500/30 bg-rose-500/10 text-rose-500";
  if (level === "high") return "border border-orange-500/30 bg-orange-500/10 text-orange-500";
  if (level === "medium") return "border border-amber-500/30 bg-amber-500/10 text-amber-500";
  return "border border-emerald-500/30 bg-emerald-500/10 text-emerald-500";
}

function cautionStatus(level: LaunchFeedItem["trade_caution_level"]) {
  if (level === "avoid") return { icon: "warning", className: "text-rose-500", label: "Avoid" } as const;
  if (level === "high") return { icon: "priority", className: "text-orange-500", label: "High caution" } as const;
  if (level === "moderate") return { icon: "info", className: "text-amber-500", label: "Volatile" } as const;
  return { icon: "verified", className: "text-emerald-500", label: "Healthy" } as const;
}

function statusLabel(item: LaunchFeedItem) {
  if (item.copycat_status === "collision") return { text: "Name collision", className: "text-orange-500" };
  if (item.copycat_status === "possible") return { text: "Copycat", className: "text-amber-500" };
  if (item.launch_quality === "likely_wash") return { text: "Likely wash", className: "text-rose-500" };
  if (item.launch_quality === "coordinated") return { text: "Coordinated", className: "text-orange-500" };
  if (item.initial_live_estimate) return { text: "Initial estimate", className: "text-primary" };
  return { text: "Original", className: "text-primary" };
}

function launchBars(item: LaunchFeedItem) {
  const tone = launchTone(item.launch_quality);
  const full = tone === "red" ? 5 : tone === "orange" ? 4 : tone === "yellow" ? 3 : tone === "green" ? 3 : 2;
  const color = tone === "red" ? "bg-rose-500" : tone === "orange" ? "bg-orange-500" : tone === "yellow" ? "bg-amber-500" : "bg-primary";
  return Array.from({ length: 5 }, (_, index) => (
    <div key={`${item.report_id}-bar-${index}`} className={`h-1 w-4 ${index < full ? color : `${color}/30`}`} />
  ));
}

function FeedTokenAvatar({
  alt,
  fallback,
  size,
  src,
}: {
  alt: string;
  fallback: string;
  size: number;
  src: string | null;
}) {
  const [hasError, setHasError] = useState(false);

  if (!src || hasError) {
    return (
      <div
        className="flex items-center justify-center rounded-full bg-primary/20 font-bold italic text-primary"
        style={{ height: size, width: size }}
      >
        {fallback}
      </div>
    );
  }

  return (
    <Image
      alt={alt}
      className="rounded-full border border-primary/20 object-cover"
      height={size}
      onError={() => setHasError(true)}
      src={src}
      unoptimized
      width={size}
    />
  );
}

export function CoinsFeedRow({ item, expanded, onToggle }: CoinsFeedRowProps) {
  const conciseSummary = summaryFallback(item);
  const caution = cautionStatus(item.trade_caution_level);
  const status = statusLabel(item);

  return (
    <div className={`overflow-hidden border-b border-primary/10 ${item.rug_risk_level === "critical" ? "bg-rose-500/5" : "bg-transparent"}`}>
      <div className="hidden cursor-pointer transition-colors hover:bg-primary/5 lg:grid lg:grid-cols-[minmax(0,1.7fr)_120px_130px_130px_150px_160px_120px_120px] lg:items-center" onClick={onToggle}>
        <div className="px-6 py-4">
          <div className="flex items-center gap-3">
            <FeedTokenAvatar alt={item.symbol} fallback={item.symbol.slice(0, 1)} size={32} src={item.logo_url} />
            <div className="min-w-0">
              <div className="font-bold text-slate-900 transition-colors group-hover:text-primary dark:text-slate-100">{item.symbol.startsWith("$") ? item.symbol : `$${item.symbol}`}</div>
              <div className="truncate text-[10px] uppercase tracking-tighter text-slate-500">{item.mint.slice(0, 4)}...{item.mint.slice(-4)}</div>
            </div>
          </div>
        </div>
        <div className="px-6 py-4 font-bold">{formatAge(item.age_minutes)}</div>
        <div className="px-6 py-4 font-bold text-primary">{formatMoney(item.liquidity_usd)}</div>
        <div className="px-6 py-4">{formatMoney(item.market_cap_usd)}</div>
        <div className="px-6 py-4">
          <span className={`rounded-full px-2 py-1 text-[10px] font-bold uppercase ${riskBadgeClass(item.rug_risk_level)}`}>
            {item.rug_risk_level === "critical" ? "Critical" : item.rug_risk_level === "high" ? "High Risk" : item.rug_risk_level === "medium" ? "Med Risk" : "Low Risk"}
          </span>
        </div>
        <div className="px-6 py-4">
          <div className={`flex items-center gap-1 ${caution.className}`}>
            <AppIcon className="h-4 w-4" name={caution.icon} />
            <span className="text-xs font-bold uppercase tracking-tighter">{caution.label}</span>
          </div>
        </div>
        <div className="px-6 py-4">
          <div className="flex gap-0.5">{launchBars(item)}</div>
        </div>
        <div className="px-6 py-4">
          <span className={`text-xs font-bold uppercase italic tracking-tighter ${status.className}`}>{status.text}</span>
        </div>
      </div>

      <div className="p-4 lg:hidden">
        <div className="flex items-start gap-3">
          <FeedTokenAvatar alt={item.symbol} fallback={item.symbol.slice(0, 1)} size={40} src={item.logo_url} />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <Link className="font-bold text-slate-900 dark:text-slate-100" href={`/report/token/${item.report_id}`}>
                {item.symbol.startsWith("$") ? item.symbol : `$${item.symbol}`}
              </Link>
              {item.initial_live_estimate ? (
                <span className="rounded-full border border-primary/20 bg-primary/10 px-2 py-1 text-[10px] font-bold uppercase text-primary">Initial estimate</span>
              ) : null}
            </div>
            <p className="mt-1 text-xs uppercase tracking-tighter text-slate-500">{item.mint.slice(0, 4)}...{item.mint.slice(-4)}</p>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{conciseSummary}</p>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <div className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2">
                <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500">Age</p>
                <p className="mt-1 font-semibold">{formatAge(item.age_minutes)}</p>
              </div>
              <div className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2">
                <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500">Liquidity</p>
                <p className="mt-1 font-semibold text-primary">{formatMoney(item.liquidity_usd)}</p>
              </div>
              <div className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2">
                <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500">Rug Risk</p>
                <span className={`mt-1 inline-flex rounded-full px-2 py-1 text-[10px] font-bold uppercase ${riskBadgeClass(item.rug_risk_level)}`}>{item.rug_risk_level}</span>
              </div>
              <div className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2">
                <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500">Trade Caution</p>
                <p className="mt-1 font-semibold">{tradeCautionLabel(item.trade_caution_level)}</p>
              </div>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <button className="rounded-lg border border-primary/20 bg-primary/10 px-4 py-2 text-xs font-bold uppercase text-primary" onClick={onToggle} type="button">
                {expanded ? "Hide" : "Preview"}
              </button>
              <Link className="rounded-lg bg-primary px-4 py-2 text-xs font-bold uppercase text-slate-50" href={`/report/token/${item.report_id}`}>
                View report
              </Link>
            </div>
          </div>
        </div>
      </div>

      {expanded ? (
        <div className="border-t border-primary/10 bg-primary/5 px-4 py-4 md:px-6">
          <div className="grid gap-3 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.95fr)_minmax(0,0.95fr)_220px]">
            <div className="rounded-xl border border-primary/20 bg-background-light p-4 dark:bg-background-dark/70">
              <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Summary</p>
              <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.summary}</p>
              <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">Updated {formatUpdated(item.updated_at)}</p>
              {item.initial_live_estimate ? (
                <p className="mt-3 rounded-xl border border-amber-500/25 bg-amber-500/10 px-3 py-2 text-xs font-semibold text-amber-500">
                  Lightweight live estimate. Open the full report for deeper analysis.
                </p>
              ) : null}
            </div>

            <div className="rounded-xl border border-primary/20 bg-background-light p-4 dark:bg-background-dark/70">
              <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Rug-risk drivers</p>
              <div className="mt-3 grid gap-2">
                {item.rug_risk_drivers.length ? (
                  item.rug_risk_drivers.map((driver) => (
                    <span key={driver} className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200">
                      {driver}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-slate-500 dark:text-slate-400">No major rug-risk driver.</p>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-primary/20 bg-background-light p-4 dark:bg-background-dark/70">
              <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Trade-caution drivers</p>
              <div className="mt-3 grid gap-2">
                {item.trade_caution_drivers.length ? (
                  item.trade_caution_drivers.map((driver) => (
                    <span key={driver} className="rounded-full border border-orange-500/25 bg-orange-500/10 px-3 py-1.5 text-xs font-semibold text-orange-500">
                      {driver}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-slate-500 dark:text-slate-400">No major trading-risk driver.</p>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-primary/20 bg-[linear-gradient(135deg,rgba(59,130,246,0.12),rgba(59,130,246,0.04))] p-4 dark:bg-[linear-gradient(135deg,rgba(37,99,235,0.22),rgba(15,23,42,0.86))]">
              <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-primary">Report actions</p>
              <div className="mt-3 space-y-3 text-sm">
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Top reducer</p>
                  <p className="mt-1 font-semibold text-slate-900 dark:text-slate-100">{item.top_reducer ?? "No material reducer"}</p>
                </div>
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Deployer</p>
                  <p className="mt-1 font-semibold text-slate-900 dark:text-slate-100">{item.deployer_short_address ?? "Unavailable"}</p>
                </div>
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Copycat</p>
                  <p className={`mt-1 font-semibold ${copycatTone(item.copycat_status) === "orange" ? "text-orange-500" : copycatTone(item.copycat_status) === "yellow" ? "text-amber-500" : "text-slate-900 dark:text-slate-100"}`}>
                    {copycatLabel(item.copycat_status)}
                  </p>
                </div>
              </div>
              <Link className="mt-5 inline-flex rounded-lg bg-primary px-4 py-2 text-sm font-bold text-slate-50" href={`/report/token/${item.report_id}`}>
                Open full report
              </Link>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
