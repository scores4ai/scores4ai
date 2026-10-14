import { useMemo, useState } from "react";
import { tools } from "@/lib/data";
import { formatUsd } from "@/lib/currency";
import { fallbackPricingForTool, formatTokenCount } from "@/lib/model-pricing";
import {
  bestValueModel,
  cheapestEquivalent,
  estimateModelCost,
  type PricingModel,
} from "@/lib/pricing";

const models: PricingModel[] = tools.slice(0, 8).map((tool) => {
  const pricing = fallbackPricingForTool({
    toolId: tool.id,
    name: tool.name,
    developer: tool.developer,
    pricing: tool.pricing,
    contextWindow: tool.contextWindow,
    valueScore: tool.scores.value,
  });

  return {
    id: tool.id,
    name: tool.name,
    scores: tool.scores,
    inputPricePerMillion: pricing.inputPerMillion,
    outputPricePerMillion: pricing.outputPerMillion,
    modelId: pricing.modelId,
    contextTokens: pricing.contextTokens,
    pricingSource: pricing.source,
  };
});

const presets = [
  { name: "Light chat", prompts: 100, input: 600, output: 200 },
  { name: "Agent workflow", prompts: 250, input: 8_000, output: 2_400 },
  { name: "Codebase audit", prompts: 25, input: 320_000, output: 48_000 },
];

export function PricingCalculator() {
  const [promptsPerDay, setPromptsPerDay] = useState(100);
  const [avgInputTokens, setAvgInputTokens] = useState(600);
  const [avgOutputTokens, setAvgOutputTokens] = useState(200);
  const [selectedModelId, setSelectedModelId] = useState(models[0].id);

  const selectedModel =
    models.find((model) => model.id === selectedModelId) ?? models[0];
  const estimate = useMemo(
    () =>
      estimateModelCost(
        { promptsPerDay, avgInputTokens, avgOutputTokens },
        selectedModel,
      ),
    [promptsPerDay, avgInputTokens, avgOutputTokens, selectedModel],
  );
  const cheapest = cheapestEquivalent(selectedModel, models);
  const bestValue = bestValueModel(models);
  const monthlyTokens = (avgInputTokens + avgOutputTokens) * promptsPerDay * 30;
  const contextFit =
    !selectedModel.contextTokens ||
    avgInputTokens + avgOutputTokens <= selectedModel.contextTokens;

  return (
    <section
      className="rounded-2xl glass p-5"
      aria-labelledby="pricing-calculator-title"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-wider text-accent">
            Pricing calculator
          </div>
          <h2
            id="pricing-calculator-title"
            className="mt-1 font-display text-2xl font-semibold"
          >
            Convert token usage into monthly API spend
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Use real per-token math: input tokens and output tokens are priced
            separately, then rolled up into daily, monthly, and yearly cost.
          </p>
        </div>
        <span className="rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-xs uppercase tracking-wider text-accent">
          OpenRouter-style pricing
        </span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {presets.map((preset) => (
          <button
            key={preset.name}
            type="button"
            onClick={() => {
              setPromptsPerDay(preset.prompts);
              setAvgInputTokens(preset.input);
              setAvgOutputTokens(preset.output);
            }}
            className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            {preset.name}
          </button>
        ))}
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <label className="text-sm">
          <span className="text-muted-foreground">Selected model</span>
          <select
            value={selectedModelId}
            onChange={(event) => setSelectedModelId(event.target.value)}
            className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-foreground outline-none focus:border-accent focus:ring-2 focus:ring-accent/25"
          >
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </label>
        <NumberField
          label="Prompts per day"
          value={promptsPerDay}
          onChange={setPromptsPerDay}
        />
        <NumberField
          label="Avg input tokens"
          value={avgInputTokens}
          onChange={setAvgInputTokens}
        />
        <NumberField
          label="Avg output tokens"
          value={avgOutputTokens}
          onChange={setAvgOutputTokens}
        />
      </div>
      <div className="mt-5 rounded-xl border border-border bg-background/40 p-4 text-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="font-medium">{selectedModel.modelId}</div>
            <div className="mt-1 text-xs text-muted-foreground">
              Context: {formatTokenCount(selectedModel.contextTokens ?? 0)} ·
              Price: {formatUsd(selectedModel.inputPricePerMillion ?? 0)} input
              / {formatUsd(selectedModel.outputPricePerMillion ?? 0)} output per
              1M tokens
            </div>
          </div>
          <span
            className={`rounded-full px-3 py-1 text-xs ${
              contextFit ? "bg-elite/10 text-elite" : "bg-broken/10 text-broken"
            }`}
          >
            {contextFit ? "Fits context" : "May exceed context"}
          </span>
        </div>
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-4">
        <Metric label="Daily cost" value={formatUsd(estimate.dailyCost)} />
        <Metric label="Monthly cost" value={formatUsd(estimate.monthlyCost)} />
        <Metric label="Yearly cost" value={formatUsd(estimate.yearlyCost)} />
        <Metric
          label="Cost / 1000 tasks"
          value={formatUsd(estimate.costPer1000Tasks)}
        />
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <InsightCard
          label="Monthly token volume"
          value={monthlyTokens.toLocaleString()}
          detail="Input + output tokens across 30 days"
        />
        <InsightCard
          label="Cheapest equivalent"
          value={cheapest?.name ?? "N/A"}
          detail={
            cheapest
              ? `${formatUsd(cheapest.inputPricePerMillion ?? 0)} / ${formatUsd(
                  cheapest.outputPricePerMillion ?? 0,
                )} per 1M`
              : "No alternative loaded"
          }
        />
        <InsightCard
          label="Best value model"
          value={bestValue?.name ?? "N/A"}
          detail="Value score divided by token price"
        />
      </div>
      <p className="mt-3 text-xs leading-5 text-muted-foreground">
        Pricing is calculated locally from bundled OpenRouter public-directory
        fallback values and transparent estimates. Connect the Supabase sync for
        live rows, cache freshness, and provider-specific pricing updates.
      </p>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-secondary/40 p-4">
      <div className="text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 font-display text-2xl font-semibold">{value}</div>
    </div>
  );
}

function InsightCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-xl bg-secondary/40 p-4 text-sm">
      <div className="text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 font-display text-xl font-semibold">{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{detail}</div>
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="text-sm">
      <span className="text-muted-foreground">{label}</span>
      <input
        type="number"
        min="0"
        step="1"
        value={value}
        onChange={(event) => onChange(Math.max(0, Number(event.target.value)))}
        className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 outline-none focus:border-accent focus:ring-2 focus:ring-accent/25"
      />
    </label>
  );
}
