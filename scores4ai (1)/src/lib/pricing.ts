export type TokenEstimateInput = {
  prompt?: string;
  inputTokens?: number;
  outputTokens?: number;
  expectedOutputTokens?: number;
  inputPricePerMillion?: number | null;
  outputPricePerMillion?: number | null;
  cachedInputPricePerMillion?: number | null;
  cachedInputTokens?: number;
  requests?: number;
};

export type CostEstimate = {
  inputTokens: number;
  outputTokens: number;
  cachedInputTokens: number;
  requests: number;
  estimatedCostUsd: number;
  formula: string;
};

const USD_PRECISION = 6;
const APPROX_CHARS_PER_TOKEN = 4;

export function estimateTokensFromText(text: string): number {
  if (!text.trim()) return 0;
  return Math.ceil(text.trim().length / APPROX_CHARS_PER_TOKEN);
}

export function estimatePromptLabCost(input: TokenEstimateInput): CostEstimate {
  const inputTokens = Math.max(
    0,
    input.inputTokens ?? estimateTokensFromText(input.prompt ?? ""),
  );
  const outputTokens = Math.max(
    0,
    input.outputTokens ?? input.expectedOutputTokens ?? 0,
  );
  const cachedInputTokens = Math.min(
    Math.max(0, input.cachedInputTokens ?? 0),
    inputTokens,
  );
  const uncachedInputTokens = inputTokens - cachedInputTokens;
  const requests = Math.max(1, input.requests ?? 1);
  const inputPrice = input.inputPricePerMillion ?? 0;
  const outputPrice = input.outputPricePerMillion ?? 0;
  const cachedInputPrice = input.cachedInputPricePerMillion ?? inputPrice;

  const cost =
    requests *
    ((uncachedInputTokens / 1_000_000) * inputPrice +
      (cachedInputTokens / 1_000_000) * cachedInputPrice +
      (outputTokens / 1_000_000) * outputPrice);

  return {
    inputTokens,
    outputTokens,
    cachedInputTokens,
    requests,
    estimatedCostUsd: Number(cost.toFixed(USD_PRECISION)),
    formula:
      "requests * ((uncachedInputTokens / 1,000,000 * inputPricePerMillion) + " +
      "(cachedInputTokens / 1,000,000 * cachedInputPricePerMillion) + " +
      "(outputTokens / 1,000,000 * outputPricePerMillion))",
  };
}

export function calculateMonthlyModelCost(
  args: TokenEstimateInput & { runsPerMonth: number },
) {
  const perRun = estimatePromptLabCost(args);
  const runsPerMonth = Math.max(0, args.runsPerMonth);
  return {
    ...perRun,
    runsPerMonth,
    monthlyCostUsd: Number(
      (perRun.estimatedCostUsd * runsPerMonth).toFixed(USD_PRECISION),
    ),
  };
}
