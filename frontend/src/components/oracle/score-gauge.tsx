"use client";

/**
 * Semicircular gauge chart for risk scores.
 * Animated fill on mount, color shifts from green → yellow → red.
 */
export function ScoreGauge({
  score,
  size = 80,
}: {
  score: number | null;
  size?: number;
}) {
  if (score === null) {
    return (
      <div
        className="flex items-center justify-center text-slate-600"
        style={{ width: size, height: size / 2 + 16 }}
      >
        <span className="text-lg font-bold">--</span>
      </div>
    );
  }

  const radius = (size - 8) / 2;
  const circumference = Math.PI * radius;
  const progress = (score / 100) * circumference;

  // Color based on score
  const getColor = (s: number) => {
    if (s <= 25) return { stroke: "#34d399", glow: "rgba(52,211,153,0.3)", text: "text-emerald-400" };
    if (s <= 50) return { stroke: "#fbbf24", glow: "rgba(251,191,36,0.3)", text: "text-amber-400" };
    if (s <= 75) return { stroke: "#f97316", glow: "rgba(249,115,22,0.3)", text: "text-orange-400" };
    return { stroke: "#f43f5e", glow: "rgba(244,63,94,0.3)", text: "text-rose-400" };
  };

  const color = getColor(score);

  return (
    <div
      className="relative flex flex-col items-center"
      style={{ width: size, height: size / 2 + 20 }}
    >
      <svg
        width={size}
        height={size / 2 + 4}
        viewBox={`0 0 ${size} ${size / 2 + 4}`}
        className="overflow-visible"
      >
        {/* Glow filter */}
        <defs>
          <filter id={`glow-${score}`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background arc */}
        <path
          d={`M 4 ${size / 2} A ${radius} ${radius} 0 0 1 ${size - 4} ${size / 2}`}
          fill="none"
          stroke="rgba(100,116,139,0.15)"
          strokeWidth={6}
          strokeLinecap="round"
        />

        {/* Progress arc */}
        <path
          d={`M 4 ${size / 2} A ${radius} ${radius} 0 0 1 ${size - 4} ${size / 2}`}
          fill="none"
          stroke={color.stroke}
          strokeWidth={6}
          strokeLinecap="round"
          strokeDasharray={`${circumference}`}
          strokeDashoffset={circumference - progress}
          filter={`url(#glow-${score})`}
          className="transition-all duration-1000 ease-out"
          style={{
            animation: "gauge-fill 1s ease-out forwards",
          }}
        />
      </svg>

      {/* Score number */}
      <div className={`absolute bottom-0 text-center ${color.text}`}>
        <span className="text-xl font-black tabular-nums leading-none">
          {score}
        </span>
      </div>
    </div>
  );
}
