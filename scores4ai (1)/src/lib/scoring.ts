import type { Tool } from "./data";

export type ScoreCategory =
  | "performance"
  | "priceValue"
  | "speed"
  | "features"
  | "privacy"
  | "communityRating";

export type ScoreSourceStatus = "Live" | "Cached" | "Estimated" | "Demo";

export type ScoreWeight = {
  key: ScoreCategory;
  label: string;
  weight: number;
  formulaInput: string;
};

export const defaultScoreWeights: ScoreWeight[] = [
  {
    key: "performance",
    label: "Performance",
    weight: 0.3,
    formulaInput: "intelligence + hallucination resistance",
  },
  {
    key: "priceValue",
    label: "Price/value",
    weight: 0.2,
    formulaInput: "value score and normalized token pricing",
  },
  {
    key: "speed",
    label: "Speed",
    weight: 0.15,
    formulaInput: "latency and throughput benchmarks",
  },
  {
    key: "features",
    label: "Features",
    weight: 0.15,
    formulaInput: "modalities, tools, context, API support",
  },
  {
    key: "privacy",
    label: "Privacy",
    weight: 0.1,
    formulaInput: "data controls, local/open-source availability",
  },
  {
    key: "communityRating",
    label: "Community rating",
    weight: 0.1,
    formulaInput: "verified reviews with abuse controls",
  },
];

export const intentOptions = [
  "coding",
  "teaching",
  "research",
  "writing",
  "automation",
  "agents",
  "students",
  "cheapest API",
  "best free AI",
  "privacy/local AI",
] as const;

export type RankingIntent = (typeof intentOptions)[number];

export const intentWeightOverrides: Record<
  RankingIntent,
  Partial<Record<ScoreCategory, number>>
> = {
  coding: {
    performance: 0.35,
    features: 0.2,
    speed: 0.15,
    priceValue: 0.15,
    privacy: 0.05,
    communityRating: 0.1,
  },
  teaching: {
    communityRating: 0.2,
    priceValue: 0.25,
    privacy: 0.15,
    performance: 0.2,
    features: 0.1,
    speed: 0.1,
  },
  research: {
    performance: 0.35,
    features: 0.2,
    privacy: 0.15,
    communityRating: 0.15,
    priceValue: 0.1,
    speed: 0.05,
  },
  writing: {
    performance: 0.3,
    communityRating: 0.2,
    features: 0.15,
    priceValue: 0.15,
    privacy: 0.1,
    speed: 0.1,
  },
  automation: {
    features: 0.3,
    speed: 0.2,
    performance: 0.2,
    priceValue: 0.15,
    privacy: 0.05,
    communityRating: 0.1,
  },
  agents: {
    features: 0.3,
    performance: 0.25,
    speed: 0.15,
    priceValue: 0.1,
    privacy: 0.1,
    communityRating: 0.1,
  },
  students: {
    priceValue: 0.35,
    communityRating: 0.2,
    privacy: 0.15,
    performance: 0.15,
    features: 0.1,
    speed: 0.05,
  },
  "cheapest API": {
    priceValue: 0.55,
    speed: 0.15,
    performance: 0.1,
    features: 0.1,
    privacy: 0.05,
    communityRating: 0.05,
  },
  "best free AI": {
    priceValue: 0.45,
    communityRating: 0.2,
    features: 0.15,
    performance: 0.1,
    privacy: 0.05,
    speed: 0.05,
  },
  "privacy/local AI": {
    privacy: 0.45,
    priceValue: 0.15,
    performance: 0.15,
    features: 0.1,
    communityRating: 0.1,
    speed: 0.05,
  },
};

export function normalizeWeights(weights: ScoreWeight[]): ScoreWeight[] {
  const total = weights.reduce((sum, item) => sum + item.weight, 0) || 1;
  return weights.map((item) => ({ ...item, weight: item.weight / total }));
}

export function weightsForIntent(intent: RankingIntent): ScoreWeight[] {
  const overrides = intentWeightOverrides[intent];
  return normalizeWeights(
    defaultScoreWeights.map((item) => ({
      ...item,
      weight: overrides[item.key] ?? item.weight,
    })),
  );
}

export function scoreInputsForTool(tool: Tool): Record<ScoreCategory, number> {
  const featureSignals = [
    tool.contextWindow ? 8 : 0,
    tool.modality?.includes("vision") ? 4 : 0,
    tool.modality?.includes("audio") ? 3 : 0,
    tool.isAgent ? 5 : 0,
    tool.openRouterId ? 5 : 0,
  ];

  return {
    performance: Math.round(
      (tool.scores.intelligence + tool.scores.hallucination) / 2,
    ),
    priceValue: tool.scores.value,
    speed: tool.scores.speed,
    features: Math.min(
      100,
      tool.scores.ease + featureSignals.reduce((a, b) => a + b, 0),
    ),
    privacy: tool.scores.privacy,
    communityRating: tool.scores.community,
  };
}

export function transparentScore(tool: Tool, weights = defaultScoreWeights) {
  const normalized = normalizeWeights(weights);
  const inputs = scoreInputsForTool(tool);
  const contributions = normalized.map((weight) => ({
    ...weight,
    input: inputs[weight.key],
    contribution: inputs[weight.key] * weight.weight,
  }));
  const score = Math.round(
    contributions.reduce((sum, item) => sum + item.contribution, 0),
  );

  return {
    score,
    contributions,
    formula:
      "Σ(category_score × normalized_weight), where category_score is 0–100 and all weights total 100%.",
    source:
      tool.sourceStatus === "demo"
        ? "Demo seed data awaiting verified benchmark, OpenRouter, and community sources"
        : "OpenRouter metadata, Supabase cache, benchmark snapshots, and verified reviews",
    confidence:
      tool.sourceStatus === "demo"
        ? "Low — demo only"
        : tool.sourceStatus === "cached"
          ? "Medium — cached"
          : "High — live metadata available",
    updatedDate: tool.lastVerified ?? "Needs live verification",
  };
}
