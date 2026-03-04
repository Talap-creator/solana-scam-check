export type RiskStatus = "low" | "medium" | "high" | "critical";
export type EntityType = "token" | "wallet" | "project";

export type RiskFactor = {
  code: string;
  severity: "low" | "medium" | "high";
  label: string;
  explanation: string;
  weight: number;
};

export type CheckReport = {
  id: string;
  entityType: EntityType;
  entityId: string;
  displayName: string;
  status: RiskStatus;
  score: number;
  confidence: number;
  summary: string;
  refreshedAt: string;
  liquidity: string;
  topHolderShare: string;
  reviewState: string;
  factors: RiskFactor[];
  metrics: Array<{ label: string; value: string }>;
  timeline: Array<{ label: string; value: string; tone?: "danger" | "warn" | "neutral" }>;
};

export const featuredReport: CheckReport = {
  id: "pearl-token",
  entityType: "token",
  entityId: "9xQeWvG816bUx9EPfEZLQ7ZL8A6V7zVYhWf9e7s6PzF1",
  displayName: "PEARL / Solana meme token",
  status: "critical",
  score: 82,
  confidence: 0.81,
  summary:
    "Высокий риск из-за активной mint authority, сильной концентрации предложения и подозрительной истории deployer.",
  refreshedAt: "4 минуты назад",
  liquidity: "$12.4K",
  topHolderShare: "87.4%",
  reviewState: "Escalated",
  factors: [
    {
      code: "TOKEN_ACTIVE_MINT_AUTHORITY",
      severity: "high",
      label: "Mint authority активна",
      explanation: "Supply токена можно изменить после запуска.",
      weight: 20,
    },
    {
      code: "TOKEN_HOLDER_CONCENTRATION",
      severity: "high",
      label: "87% у top 10 holders",
      explanation: "Критичная концентрация предложения у ограниченного круга адресов.",
      weight: 18,
    },
    {
      code: "PROJECT_NEW_DOMAIN",
      severity: "medium",
      label: "Новый домен проекта",
      explanation: "Связанный сайт зарегистрирован менее 14 дней назад.",
      weight: 9,
    },
  ],
  metrics: [
    { label: "Score", value: "82" },
    { label: "Confidence", value: "0.81" },
    { label: "Top 10 share", value: "87.4%" },
    { label: "Liquidity", value: "$12.4K" },
  ],
  timeline: [
    { label: "Active mint authority", value: "Detected", tone: "danger" },
    { label: "Linked deployer history", value: "3 suspicious launches", tone: "danger" },
    { label: "Project domain age", value: "12 days", tone: "warn" },
    { label: "Background refresh", value: "In progress", tone: "neutral" },
  ],
};

export const dashboardHistory: CheckReport[] = [
  featuredReport,
  {
    id: "wallet-alpha",
    entityType: "wallet",
    entityId: "8PX1DbLyJQzY63K5kTz2S88xJ5UQh1dBnmfV91rYx4cR",
    displayName: "Wallet / 8PX1...x4cR",
    status: "high",
    score: 67,
    confidence: 0.77,
    summary: "Повторяющийся launch-dump паттерн и связи с ранее flagged токенами.",
    refreshedAt: "18 минут назад",
    liquidity: "n/a",
    topHolderShare: "n/a",
    reviewState: "Queued",
    factors: [
      {
        code: "WALLET_LINKED_FLAGGED",
        severity: "high",
        label: "Связь с flagged entities",
        explanation: "Кошелек взаимодействовал с несколькими адресами из risk lists.",
        weight: 16,
      },
      {
        code: "WALLET_LAUNCH_DUMP",
        severity: "high",
        label: "Launch-dump behavior",
        explanation: "Повторяющийся шаблон запуска и быстрого слива ликвидности.",
        weight: 18,
      },
    ],
    metrics: [
      { label: "Score", value: "67" },
      { label: "Confidence", value: "0.77" },
      { label: "Linked flags", value: "5" },
      { label: "Age", value: "41 days" },
    ],
    timeline: [
      { label: "Flagged links", value: "5 matches", tone: "danger" },
      { label: "Recent launch pattern", value: "Detected", tone: "danger" },
      { label: "Last active", value: "2 hours ago", tone: "neutral" },
      { label: "Background refresh", value: "Complete", tone: "neutral" },
    ],
  },
  {
    id: "project-orbit",
    entityType: "project",
    entityId: "orbit-project",
    displayName: "Orbit Project",
    status: "medium",
    score: 42,
    confidence: 0.63,
    summary: "Данных недостаточно для высокого риска, но trust signals проекта слабые.",
    refreshedAt: "1 час назад",
    liquidity: "$58K",
    topHolderShare: "54.1%",
    reviewState: "Watching",
    factors: [
      {
        code: "PROJECT_THIN_SOCIALS",
        severity: "medium",
        label: "Слабый social presence",
        explanation: "Низкая активность и неполная project metadata.",
        weight: 8,
      },
      {
        code: "PROJECT_LOW_CONFIDENCE",
        severity: "medium",
        label: "Недостаточно confidence",
        explanation: "Часть источников данных недоступна или пуста.",
        weight: 6,
      },
    ],
    metrics: [
      { label: "Score", value: "42" },
      { label: "Confidence", value: "0.63" },
      { label: "Liquidity", value: "$58K" },
      { label: "Domain age", value: "72 days" },
    ],
    timeline: [
      { label: "Social validation", value: "Weak", tone: "warn" },
      { label: "Domain age", value: "72 days", tone: "neutral" },
      { label: "Liquidity", value: "Stable", tone: "neutral" },
      { label: "Background refresh", value: "Pending", tone: "neutral" },
    ],
  },
];

export const statusTone: Record<RiskStatus, string> = {
  low: "bg-emerald-100 text-emerald-800",
  medium: "bg-amber-100 text-amber-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-[linear-gradient(135deg,#a9341e,#c84b31)] text-white",
};
