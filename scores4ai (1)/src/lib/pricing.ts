import type { Tool } from "./data";

export type PricingModel = Pick<Tool, "id" | "name" | "scores"> & {
  inputPricePerMillion?: number;
  outputPricePerMillion?: number;
  modelId?: string;
  contextTokens?: number;
  pricingSource?: "openrouter-snapshot" | "local-estimate";
};

export type PricingInputs = {
  promptsPerDay: number;
  avgInputTokens: number;
  avgOutputTokens: number;
};

export function estimateTokensFromText(text: string) {
  return Math.max(1, Math.ceil(text.trim().length / 4));
}

export function estimateModelCost(inputs: PricingInputs, model: PricingModel) {
  const inputCostPerTask =
    (inputs.avgInputTokens / 1_000_000) * (model.inputPricePerMillion ?? 0);
  const outputCostPerTask =
    (inputs.avgOutputTokens / 1_000_000) * (model.outputPricePerMillion ?? 0);
  const taskCost = inputCostPerTask + outputCostPerTask;
  const dailyCost = taskCost * inputs.promptsPerDay;
  return {
    taskCost,
    dailyCost,
    monthlyCost: dailyCost * 30,
    yearlyCost: dailyCost * 365,
    costPer1000Tasks: taskCost * 1000,
  };
}

export function cheapestEquivalent(
  selected: PricingModel,
  models: PricingModel[],
) {
  return [...models]
    .filter((model) => model.id !== selected.id)
    .sort(
      (a, b) =>
        (a.inputPricePerMillion ?? Number.POSITIVE_INFINITY) +
        (a.outputPricePerMillion ?? Number.POSITIVE_INFINITY) -
        ((b.inputPricePerMillion ?? Number.POSITIVE_INFINITY) +
          (b.outputPricePerMillion ?? Number.POSITIVE_INFINITY)),
    )[0];
}

export function bestValueModel(models: PricingModel[]) {
  return [...models].sort((a, b) => {
    const aPrice =
      (a.inputPricePerMillion ?? 0) + (a.outputPricePerMillion ?? 0) || 1;
    const bPrice =
      (b.inputPricePerMillion ?? 0) + (b.outputPricePerMillion ?? 0) || 1;
    return b.scores.value / bPrice - a.scores.value / aPrice;
  })[0];
}
