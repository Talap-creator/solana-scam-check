"use client";

/**
 * Tiny SVG sparkline for score history.
 * Points are rendered oldest→newest left→right.
 * Color reflects the latest score value.
 */

type Point = { score: number; published_at: string };

function scoreStroke(score: number) {
  if (score <= 25) return "#34d399"; // emerald
  if (score <= 50) return "#fbbf24"; // amber
  if (score <= 75) return "#f97316"; // orange
  return "#f43f5e"; // rose
}

export function ScoreSparkline({
  points,
  width = 80,
  height = 28,
}: {
  points: Point[];
  width?: number;
  height?: number;
}) {
  if (points.length < 2) {
    return (
      <div
        className="flex items-center justify-center text-[10px] text-slate-600"
        style={{ width, height }}
      >
        {points.length === 1 ? (
          <span className="font-bold text-slate-400">{points[0].score}</span>
        ) : (
          "–"
        )}
      </div>
    );
  }

  const pad = 3;
  const w = width - pad * 2;
  const h = height - pad * 2;

  const scores = points.map((p) => p.score);
  const min = Math.max(0, Math.min(...scores) - 5);
  const max = Math.min(100, Math.max(...scores) + 5);
  const range = max - min || 1;

  const toX = (i: number) => pad + (i / (points.length - 1)) * w;
  const toY = (s: number) => pad + h - ((s - min) / range) * h;

  const pathD = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${toX(i).toFixed(1)} ${toY(p.score).toFixed(1)}`)
    .join(" ");

  // Area fill path
  const areaD =
    pathD +
    ` L ${toX(points.length - 1).toFixed(1)} ${(pad + h).toFixed(1)}` +
    ` L ${toX(0).toFixed(1)} ${(pad + h).toFixed(1)} Z`;

  const latest = points[points.length - 1].score;
  const stroke = scoreStroke(latest);
  const gradId = `spark-grad-${width}-${points.length}`;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.18" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Area */}
      <path d={areaD} fill={`url(#${gradId})`} />

      {/* Line */}
      <path
        d={pathD}
        fill="none"
        stroke={stroke}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Latest dot */}
      <circle
        cx={toX(points.length - 1)}
        cy={toY(latest)}
        r={2.5}
        fill={stroke}
        opacity={0.9}
      />
    </svg>
  );
}
