export type PricingSource = "openrouter-snapshot" | "local-estimate";

export type ModelPricing = {
  toolId: string;
  modelId: string;
  displayName: string;
  provider: string;
  contextTokens: number;
  inputPerMillion: number;
  outputPerMillion: number;
  source: PricingSource;
  updatedLabel: string;
};

export const openRouterPricingSnapshot: ModelPricing[] = [
  {
    toolId: "gpt-5",
    modelId: "openai/gpt-4.1",
    displayName: "OpenAI GPT-4.1",
    provider: "OpenAI",
    contextTokens: 1_000_000,
    inputPerMillion: 2,
    outputPerMillion: 8,
    source: "openrouter-snapshot",
    updatedLabel: "OpenRouter public model directory fallback",
  },
  {
    toolId: "claude-4",
    modelId: "anthropic/claude-sonnet-4",
    displayName: "Claude Sonnet 4 class",
    provider: "Anthropic",
    contextTokens: 200_000,
    inputPerMillion: 3,
    outputPerMillion: 15,
    source: "openrouter-snapshot",
    updatedLabel: "OpenRouter public model directory fallback",
  },
  {
    toolId: "gemini-3",
    modelId: "google/gemini-2.5-pro",
    displayName: "Gemini 2.5 Pro",
    provider: "Google",
    contextTokens: 1_000_000,
    inputPerMillion: 1.25,
    outputPerMillion: 10,
    source: "openrouter-snapshot",
    updatedLabel: "OpenRouter public model directory fallback",
  },
  {
    toolId: "deepseek-v3",
    modelId: "deepseek/deepseek-chat",
    displayName: "DeepSeek Chat",
    provider: "DeepSeek",
    contextTokens: 128_000,
    inputPerMillion: 0.27,
    outputPerMillion: 1.1,
    source: "openrouter-snapshot",
    updatedLabel: "OpenRouter public model directory fallback",
  },
  {
    toolId: "llama-4",
    modelId: "meta-llama/llama-3.3-70b-instruct",
    displayName: "Llama 3.3 70B Instruct",
    provider: "Meta",
    contextTokens: 131_000,
    inputPerMillion: 0.12,
    outputPerMillion: 0.3,
    source: "openrouter-snapshot",
    updatedLabel: "OpenRouter public model directory fallback",
  },
  {
    toolId: "mistral-large",
    modelId: "mistralai/mistral-large",
    displayName: "Mistral Large",
    provider: "Mistral",
    contextTokens: 128_000,
    inputPerMillion: 2,
    outputPerMillion: 6,
    source: "openrouter-snapshot",
    updatedLabel: "OpenRouter public model directory fallback",
  },
];

export function pricingForTool(toolId: string) {
  return openRouterPricingSnapshot.find((row) => row.toolId === toolId);
}

export function fallbackPricingForTool(input: {
  toolId: string;
  name: string;
  developer: string;
  pricing: string;
  contextWindow?: string;
  valueScore: number;
}): ModelPricing {
  const snapshot = pricingForTool(input.toolId);
  if (snapshot) return snapshot;

  const isOpenSource = input.pricing === "Open Source";
  return {
    toolId: input.toolId,
    modelId: `scores4ai/${input.toolId}`,
    displayName: input.name,
    provider: input.developer,
    contextTokens: parseContextWindow(input.contextWindow),
    inputPerMillion: isOpenSource ? 0 : input.valueScore > 90 ? 0.2 : 3,
    outputPerMillion: isOpenSource ? 0 : input.valueScore > 90 ? 0.6 : 15,
    source: "local-estimate",
    updatedLabel: "Scores4AI estimate until OpenRouter sync matches this row",
  };
}

export function parseContextWindow(value?: string) {
  if (!value) return 0;
  const normalized = value.trim().toLowerCase();
  const numeric = Number.parseFloat(normalized.replace(/[^0-9.]/g, ""));
  if (!Number.isFinite(numeric)) return 0;
  if (normalized.includes("m")) return Math.round(numeric * 1_000_000);
  if (normalized.includes("k")) return Math.round(numeric * 1_000);
  return Math.round(numeric);
}

export function formatTokenCount(value: number) {
  if (!value) return "Unknown";
  if (value >= 1_000_000) return `${value / 1_000_000}M tokens`;
  if (value >= 1_000) return `${Math.round(value / 1_000)}K tokens`;
  return `${value.toLocaleString()} tokens`;
}
