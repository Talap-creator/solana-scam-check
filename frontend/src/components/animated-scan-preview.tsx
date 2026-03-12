"use client";

import { useEffect, useMemo, useState } from "react";

type PreviewItem = {
  displayName: string;
  status: string;
};

type AnimatedScanPreviewProps = {
  items: PreviewItem[];
};

const progressStops = [0, 24, 46, 68, 86];

export function AnimatedScanPreview({ items }: AnimatedScanPreviewProps) {
  const queue = useMemo(
    () =>
      items.length > 0
        ? items
        : [{ displayName: "LINK / Chainlink Token", status: "LOW" }],
    [items],
  );
  const [itemIndex, setItemIndex] = useState(0);
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      window.setTimeout(() => setPhase(1), 240),
      window.setTimeout(() => setPhase(2), 760),
      window.setTimeout(() => setPhase(3), 1280),
      window.setTimeout(() => setPhase(4), 1800),
      window.setTimeout(() => {
        setPhase(0);
        setItemIndex((current) => (current + 1) % queue.length);
      }, 3200),
    ];

    return () => {
      for (const timer of timers) {
        window.clearTimeout(timer);
      }
    };
  }, [itemIndex, queue.length]);

  const current = queue[itemIndex];
  const lines = [
    `> Initiating Deep Scan: ${current.displayName}`,
    "> Analyzing Contract Ownership... [VERIFIED]",
    "> Checking Liquidity Burn... [100.00%]",
    `> Scoring Risk Profile... [${current.status.toUpperCase()}]`,
  ];

  return (
    <>
      <div className="space-y-2 font-mono text-sm text-[#3b82f6]/85">
        {lines.map((line, index) => (
          <p
            key={`${current.displayName}-${line}`}
            className={`scan-terminal-line transition-all duration-500 ${
              phase > index ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
            }`}
          >
            {line}
          </p>
        ))}
      </div>
      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-[#3b82f6]/10">
        <div
          className="scan-progress-glow h-full rounded-full bg-[#3b82f6] transition-[width] duration-500"
          style={{ width: `${progressStops[phase]}%` }}
        />
      </div>
    </>
  );
}
