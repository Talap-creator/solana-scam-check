"use client";

/**
 * Animated AI Agent mascot - a pulsing brain/shield icon with breathing glow.
 * Three states: idle (cyan pulse), scanning (green fast pulse), alert (red glow).
 */
export function AgentMascot({
  state = "idle",
  size = "lg",
}: {
  state?: "idle" | "scanning" | "alert";
  size?: "sm" | "lg";
}) {
  const sizeClass = size === "lg" ? "h-20 w-20" : "h-10 w-10";
  const glowSize = size === "lg" ? "h-24 w-24" : "h-14 w-14";

  const colors = {
    idle: {
      glow: "bg-cyan-500/20",
      ring: "border-cyan-500/40",
      icon: "text-cyan-400",
      anim: "animate-[breathe_3s_ease-in-out_infinite]",
    },
    scanning: {
      glow: "bg-emerald-500/25",
      ring: "border-emerald-500/50",
      icon: "text-emerald-400",
      anim: "animate-[breathe_1.5s_ease-in-out_infinite]",
    },
    alert: {
      glow: "bg-rose-500/25",
      ring: "border-rose-500/50",
      icon: "text-rose-400",
      anim: "animate-[breathe_1s_ease-in-out_infinite]",
    },
  };

  const c = colors[state];

  return (
    <div className="relative flex items-center justify-center">
      {/* Outer glow */}
      <div
        className={`absolute ${glowSize} rounded-full ${c.glow} ${c.anim} blur-xl`}
      />
      {/* Ring */}
      <div
        className={`absolute ${sizeClass} rounded-full border-2 ${c.ring} ${c.anim}`}
      />
      {/* Icon container */}
      <div
        className={`relative flex ${sizeClass} items-center justify-center rounded-full bg-[rgba(15,23,42,0.9)] backdrop-blur-sm`}
      >
        {/* Brain/AI icon */}
        <svg
          className={`${size === "lg" ? "h-10 w-10" : "h-5 w-5"} ${c.icon} transition-colors duration-500`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z"
          />
        </svg>
        {/* Scanning indicator dots */}
        {state === "scanning" && (
          <div className="absolute -bottom-1 flex gap-1">
            <span className="h-1.5 w-1.5 animate-[bounce_1s_infinite_0ms] rounded-full bg-emerald-400" />
            <span className="h-1.5 w-1.5 animate-[bounce_1s_infinite_200ms] rounded-full bg-emerald-400" />
            <span className="h-1.5 w-1.5 animate-[bounce_1s_infinite_400ms] rounded-full bg-emerald-400" />
          </div>
        )}
      </div>
    </div>
  );
}
