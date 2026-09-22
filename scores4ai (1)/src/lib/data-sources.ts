export const MODEL_FRESHNESS_HOURS = 12;
export const PRICING_FRESHNESS_HOURS = 24;
export const DATA_FRESHNESS_MINUTES = MODEL_FRESHNESS_HOURS * 60;

export type DataSourceStatus = "demo" | "live" | "cached" | "estimated";

export const dataSourceCopy: Record<
  DataSourceStatus,
  { label: string; helper: string }
> = {
  demo: {
    label: "Seed data — clearly labeled",
    helper:
      "This workspace is usable for comparison flows today, but bundled scores are seed records. Trust the label on each card: live and cached rows come from OpenRouter + Supabase; estimated rows disclose their assumptions.",
  },
  live: {
    label: "Live data",
    helper:
      "Fresh OpenRouter metadata was fetched and merged with cached benchmark signals.",
  },
  cached: {
    label: "Cached data",
    helper:
      "Live sources were unavailable, so the latest Supabase cache snapshot is being shown.",
  },
  estimated: {
    label: "Estimated",
    helper:
      "This value is calculated from public metadata and transparent assumptions until a verified live measurement is available.",
  },
};

export const scoringDimensions = [
  {
    key: "ai",
    label: "AI Score",
    weight: 0.5,
    description:
      "Transparent comprehensive benchmarks: capability, speed, reliability, hallucination resistance, privacy, and cost/value.",
  },
  {
    key: "community",
    label: "Community Score",
    weight: 0.3,
    description:
      "Verified user ratings with anti-spam weighting, recency decay, and outlier detection.",
  },
  {
    key: "programmer",
    label: "Programmer Score",
    weight: 0.2,
    description:
      "Vetted member reviews from builders who ship production code with the model, tool, or agent.",
  },
] as const;

export function getTransparentScore(input: {
  benchmark: number;
  community: number;
  programmer: number;
}) {
  return Math.round(
    input.benchmark * scoringDimensions[0].weight +
      input.community * scoringDimensions[1].weight +
      input.programmer * scoringDimensions[2].weight,
  );
}
