import { useMemo, useState } from "react";
import { catalogTools as tools } from "@/lib/catalog";
import { formatUsd } from "@/lib/currency";
import {
  bestValueModel,
  cheapestEquivalent,
  estimateModelCost,
  type PricingModel,
} from "@/lib/pricing";

const models: PricingModel[] = tools.slice(0, 8).map((tool) => ({
  id: tool.id,
  name: tool.name,
  scores: tool.scores,
  inputPricePerMillion:
    tool.pricing === "Open Source" ? 0 : tool.scores.value > 90 ? 0.2 : 3,
  outputPricePerMillion:
    tool.pricing === "Open Source" ? 0 : tool.scores.value > 90 ? 0.6 : 15,
}));

const presets = [
  { name: "Light chat", prompts: 100, input: 600, output: 200 },
  { name: "Agent workflow", prompts: 250, input: 8_000, output: 2_400 },
  { name: "Codebase audit", prompts: 25, input: 320_000, output: 48_000 },
];

export function PricingCalculator() {
  const [promptsPerDay, setPromptsPerDay] = useState(100);
  const [avgInputTokens, setAvgInputTokens] = useState(600);
  const [avgOutputTokens, setAvgOutputTokens] = useState(200);
  const [selectedModelId, setSelectedModelId] = useState(models[0]?.id ?? "");

  const selectedModel =
    models.find((model) => model.id === selectedModelId) ?? models[0];

  if (!selectedModel) {
    return (
      <section className="rounded-2xl glass p-5">
        <h2 className="font-display text-2xl font-semibold">Pricing calculator</h2>
        <p className="mt-2 text-sm text-muted-foreground">No live models available yet.</p>
      </section>
    );
  }
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
            Estimate API spend before you switch
          </h2>
        </div>
        <span className="rounded-full border border-border px-3 py-1 text-xs uppercase tracking-wider text-muted-foreground">
          Estimated pricing
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
          label="Avg prompt size (tokens)"
          value={avgInputTokens}
          onChange={setAvgInputTokens}
        />
        <NumberField
          label="Avg output size (tokens)"
          value={avgOutputTokens}
          onChange={setAvgOutputTokens}
        />
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
      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <div className="rounded-xl bg-secondary/40 p-4 text-sm">
          <div className="text-xs uppercase tracking-wider text-muted-foreground">
            Cheapest equivalent model
          </div>
          <div className="mt-1 font-display text-2xl font-semibold">
            {cheapest?.name ?? "N/A"}
          </div>
        </div>
        <div className="rounded-xl bg-secondary/40 p-4 text-sm">
          <div className="text-xs uppercase tracking-wider text-muted-foreground">
            Best value model
          </div>
          <div className="mt-1 font-display text-2xl font-semibold">
            {bestValue?.name ?? "N/A"}
          </div>
        </div>
      </div>
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
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-foreground outline-none focus:border-accent focus:ring-2 focus:ring-accent/25"
      />
    </label>
  );
}
