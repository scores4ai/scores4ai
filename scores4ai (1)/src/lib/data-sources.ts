export const MODEL_FRESHNESS_HOURS = 12;
export const PRICING_FRESHNESS_HOURS = 24;
export const DATA_FRESHNESS_MINUTES = MODEL_FRESHNESS_HOURS * 60;

export type DataSourceStatus = "demo" | "live" | "cached" | "estimated";

export const dataSourceCopy: Record<
  DataSourceStatus,
  { label: string; helper: string }
> = {
  demo: {
    label: "Demo seed data",
    helper:
      "Scores in the bundled catalog are example records for UI validation. Production rankings should come from OpenRouter metadata, Supabase-cached benchmarks, verified community ratings, and vetted programmer reviews.",
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

type DataSourceEnv = Record<string, string | boolean | undefined>;

const statusValues = new Set<DataSourceStatus>([
  "demo",
  "live",
  "cached",
  "estimated",
]);

function normalizeStatus(value: string | boolean | undefined) {
  if (typeof value !== "string") return undefined;
  const normalized = value.trim().toLowerCase();
  return statusValues.has(normalized as DataSourceStatus)
    ? (normalized as DataSourceStatus)
    : undefined;
}

function isEnabled(value: string | boolean | undefined) {
  if (typeof value === "boolean") return value;
  if (typeof value !== "string") return false;
  return ["1", "true", "yes", "on", "live", "enabled"].includes(
    value.trim().toLowerCase(),
  );
}

export function resolveConfiguredDataSourceStatus(
  env: DataSourceEnv = import.meta.env,
): DataSourceStatus {
  const explicitStatus =
    normalizeStatus(env.VITE_DATA_SOURCE_STATUS) ??
    normalizeStatus(env.VITE_PUBLIC_DATA_SOURCE_STATUS);
  if (explicitStatus) return explicitStatus;

  if (isEnabled(env.VITE_OPENROUTER_LIVE_DATA)) return "live";

  const hasPublicSupabaseConfig = Boolean(env.VITE_SUPABASE_URL);
  if (hasPublicSupabaseConfig) return "cached";

  return "demo";
}

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
