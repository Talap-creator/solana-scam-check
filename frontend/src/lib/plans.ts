export type SupportedPlan = "free" | "pro" | "enterprise";

export const APP_TELEGRAM_URL = "https://t.me/mrtalap";

type PlanMeta = {
  cadence: string;
  dailyLimitLabel: string;
  label: string;
  price: string;
  summary: string;
};

const PLAN_META: Record<SupportedPlan, PlanMeta> = {
  free: {
    cadence: "/month",
    dailyLimitLabel: "5 requests/day",
    label: "Freemium",
    price: "$0",
    summary: "Starter access for launch checks and basic platform usage.",
  },
  pro: {
    cadence: "/month",
    dailyLimitLabel: "200 requests/day",
    label: "Premium",
    price: "$100",
    summary: "Full token workflow for active traders and small teams.",
  },
  enterprise: {
    cadence: "",
    dailyLimitLabel: "Custom limits",
    label: "Enterprise",
    price: "Custom",
    summary: "Tailored onboarding, limits, and support for serious operators.",
  },
};

function normalizePlan(plan: string): SupportedPlan {
  if (plan === "pro") {
    return "pro";
  }
  if (plan === "enterprise") {
    return "enterprise";
  }
  return "free";
}

export function getPlanMeta(plan: string): PlanMeta {
  return PLAN_META[normalizePlan(plan)];
}

export function formatPlanLabel(plan: string): string {
  return getPlanMeta(plan).label;
}
