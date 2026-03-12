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
  name?: string | null;
  symbol?: string | null;
  logoUrl?: string | null;
  status: RiskStatus;
  score: number;
  rugProbability: number;
  technicalRisk: number;
  distributionRisk: number;
  marketExecutionRisk: number;
  behaviourRisk: number;
  marketMaturity: number;
  pageMode: "early_launch" | "early_market" | "mature";
  launchRisk: {
    score: number;
    level: "unknown" | "low" | "medium" | "high" | "critical";
    summary: string;
    drivers: string[];
  };
  earlyWarnings: string[];
  launchRadar: {
    launchAgeMinutes: number | null;
    initialLiquidityBand: string;
    earlyTradePressure: "low" | "balanced" | "aggressive";
    launchConcentration: "low" | "medium" | "high";
    copycatStatus: "none" | "possible" | "collision";
    earlyClusterActivity: "none" | "watch" | "suspicious";
    summary: string;
  };
  marketSource?: string | null;
  tradeCaution?: {
    score: number;
    level: "low" | "moderate" | "high" | "avoid";
    label: string;
    summary: string;
    drivers: string[];
    dimensions: {
      adminCaution: number;
      executionCaution: number;
      concentrationCaution: number;
      behaviouralCaution: number;
      marketStructureStrength: number;
    };
  };
  confidence: number;
  summary: string;
  refreshedAt: string;
  liquidity: string;
  topHolderShare: string;
  reviewState: string;
  riskBreakdown: Array<{
    block: string;
    score: number;
    weight: number;
    weightedScore: number;
    kind?: "risk" | "positive";
  }>;
  factors: RiskFactor[];
  riskIncreasers: RiskFactor[];
  riskReducers: RiskFactor[];
  behaviourAnalysisV2?: {
    summary: string;
    overallBehaviourRisk: RiskStatus;
    confidence: "limited" | "medium" | "high";
    score: number;
    modules: Record<
      string,
      {
        status: "clear" | "watch" | "flagged";
        severity: "low" | "medium" | "high";
        score: number;
        summary: string;
        details: string[];
        evidence: Record<string, string | number | boolean | null>;
        confidence: "limited" | "medium" | "high";
      }
    >;
    confidenceBreakdown: {
      holderCoverage: "full" | "partial" | "limited";
      transactionCoverage: "full" | "partial" | "limited";
      fundingTraceDepth: "shallow" | "moderate" | "deep";
      liquidityData: "full" | "partial" | "limited";
    };
    version: string;
  };
  behaviourAnalysis: Array<{
    key: string;
    title: string;
    status: string;
    summary: string;
    tone: "green" | "yellow" | "orange" | "red";
    details: string[];
  }>;
  metrics: Array<{ label: string; value: string }>;
  timeline: Array<{ label: string; value: string; tone?: "danger" | "warn" | "neutral" }>;
};

export const statusTone: Record<RiskStatus, string> = {
  low: "bg-emerald-100 text-emerald-800",
  medium: "bg-amber-100 text-amber-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-[linear-gradient(135deg,#a9341e,#c84b31)] text-white",
};
