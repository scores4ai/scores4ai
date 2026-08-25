import { useMemo, useState } from "react";
import { tools } from "@/lib/data";
import { formatUsd } from "@/lib/currency";
import { fallbackPricingForTool, formatTokenCount } from "@/lib/model-pricing";
import { estimateTokensFromText } from "@/lib/pricing";

const modelDefaults = tools.slice(0, 6).map((tool) => {
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
    modelId: pricing.modelId,
    contextWindow: formatTokenCount(pricing.contextTokens),
    contextTokens: pricing.contextTokens,
    speed: tool.scores.speed,
    formatting: tool.scores.ease,
    reasoning: tool.scores.intelligence,
    hallucinationRisk: 100 - tool.scores.hallucination,
    citations: tool.tags.includes("research") || tool.tags.includes("search"),
    inputPrice: pricing.inputPerMillion,
    outputPrice: pricing.outputPerMillion,
    source: pricing.source,
  };
});

const promptPresets = [
  {
    name: "Coding agent",
    prompt:
      "Audit this TypeScript repository for production blockers. Return prioritized fixes, risk level, affected files, and cost assumptions.",
    output: 1_200,
  },
  {
    name: "Research answer",
    prompt:
      "Research whether a startup should use open-weight or hosted frontier models. Include citations needed, uncertainty, and a recommendation.",
    output: 900,
  },
  {
    name: "Support triage",
    prompt:
      "Classify these customer tickets by urgency, summarize next action, and identify where hallucination would create business risk.",
    output: 500,
  },
];

export function PromptLab() {
  const [prompt, setPrompt] = useState(promptPresets[0].prompt);
  const [selected, setSelected] = useState<string[]>(
    modelDefaults.slice(0, 3).map((model) => model.id),
  );
  const [expectedOutputTokens, setExpectedOutputTokens] = useState(
    promptPresets[0].output,
  );

  const inputTokens = useMemo(() => estimateTokensFromText(prompt), [prompt]);
  const selectedModels = modelDefaults.filter((model) =>
    selected.includes(model.id),
  );
  const rankedModels = useMemo(
    () =>
      selectedModels
        .map((model) => {
          const cost =
            (inputTokens / 1_000_000) * model.inputPrice +
            (expectedOutputTokens / 1_000_000) * model.outputPrice;
          const riskPenalty = model.hallucinationRisk * 0.18;
          const qualityScore = Math.round(
            model.reasoning * 0.45 +
              model.formatting * 0.2 +
              model.speed * 0.15 +
              (model.citations ? 8 : 0) -
              riskPenalty,
          );

          return { ...model, cost, qualityScore };
        })
        .sort((a, b) => b.qualityScore - a.qualityScore),
    [expectedOutputTokens, inputTokens, selectedModels],
  );
  const recommendedModel = rankedModels[0];
  const cheapestModel = [...rankedModels].sort((a, b) => a.cost - b.cost)[0];

  function toggleModel(id: string) {
    setSelected((current) => {
      if (current.includes(id)) {
        return current.length === 1
          ? current
          : current.filter((modelId) => modelId !== id);
      }
      return [...current, id];
    });
  }

  return (
    <section
      className="rounded-2xl glass p-5"
      aria-labelledby="prompt-lab-title"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-wider text-accent">
            Prompt Lab
          </div>
          <h2
            id="prompt-lab-title"
            className="mt-1 font-display text-2xl font-semibold"
          >
            Price and quality-check one prompt before you run it
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Paste a task, choose candidate models, and compare token budget,
            OpenRouter price fields, context fit, and risk signals in one table.
          </p>
        </div>
        <span className="rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-xs uppercase tracking-wider text-accent">
          No API call made
        </span>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {promptPresets.map((preset) => (
          <button
            key={preset.name}
            type="button"
            onClick={() => {
              setPrompt(preset.prompt);
              setExpectedOutputTokens(preset.output);
            }}
            className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            {preset.name}
          </button>
        ))}
      </div>

      <label className="mt-5 block text-sm">
        <span className="text-muted-foreground">Evaluation prompt</span>
        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          className="mt-1 min-h-32 w-full rounded-xl border border-border bg-background/60 p-4 text-sm leading-6 text-foreground outline-none focus:border-accent focus:ring-2 focus:ring-accent/25"
        />
      </label>

      <div className="mt-4 grid gap-4 md:grid-cols-[1fr_220px]">
        <div>
          <div className="text-sm text-muted-foreground">Select models</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {modelDefaults.map((model) => (
              <button
                key={model.id}
                type="button"
                onClick={() => toggleModel(model.id)}
                className={`rounded-full border px-3 py-1.5 text-xs transition-colors ${
                  selected.includes(model.id)
                    ? "border-accent bg-accent text-accent-foreground"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                {model.name}
              </button>
            ))}
          </div>
        </div>
        <label className="text-sm">
          <span className="text-muted-foreground">Expected output tokens</span>
          <input
            type="number"
            min="1"
            value={expectedOutputTokens}
            onChange={(event) =>
              setExpectedOutputTokens(Math.max(1, Number(event.target.value)))
            }
            className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 outline-none focus:border-accent focus:ring-2 focus:ring-accent/25"
          />
        </label>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <DecisionMetric
          label="Input tokens"
          value={inputTokens.toLocaleString()}
          detail="Estimated from prompt length"
        />
        <DecisionMetric
          label="Best quality fit"
          value={recommendedModel?.name ?? "Select a model"}
          detail={
            recommendedModel
              ? `Risk-adjusted score ${recommendedModel.qualityScore}/100`
              : ""
          }
        />
        <DecisionMetric
          label="Lowest run cost"
          value={cheapestModel ? formatUsd(cheapestModel.cost) : "—"}
          detail={cheapestModel?.name ?? "Select a model"}
        />
      </div>

      <div className="mt-5 overflow-x-auto rounded-xl border border-border">
        <table className="w-full min-w-[860px] text-left text-sm">
          <thead className="bg-secondary/60 text-xs uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Tokens</th>
              <th className="px-4 py-3">Run cost</th>
              <th className="px-4 py-3">OpenRouter price / 1M</th>
              <th className="px-4 py-3">Context fit</th>
              <th className="px-4 py-3">Decision signals</th>
            </tr>
          </thead>
          <tbody>
            {rankedModels.map((model) => {
              const totalTokens = inputTokens + expectedOutputTokens;
              const fitsContext =
                model.contextTokens === 0 || totalTokens <= model.contextTokens;
              return (
                <tr key={model.id} className="border-t border-border">
                  <td className="px-4 py-3">
                    <div className="font-medium">{model.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {model.modelId}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {inputTokens.toLocaleString()} in /{" "}
                    {expectedOutputTokens.toLocaleString()} out
                  </td>
                  <td className="px-4 py-3 font-medium">
                    {formatUsd(model.cost)}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {formatUsd(model.inputPrice)} in ·{" "}
                    {formatUsd(model.outputPrice)} out
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-1 text-xs ${
                        fitsContext
                          ? "bg-elite/10 text-elite"
                          : "bg-broken/10 text-broken"
                      }`}
                    >
                      {fitsContext ? "Fits" : "Too long"}
                    </span>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {model.contextWindow}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    Quality {model.qualityScore}/100 · Speed {model.speed}/100 ·
                    Hallucination risk {model.hallucinationRisk}/100 · Citations{" "}
                    {model.citations ? "likely" : "not verified"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs leading-5 text-muted-foreground">
        Pricing rows marked with OpenRouter model IDs use bundled public
        directory fallback values until the scheduled Supabase sync is
        connected; no prompt content leaves this browser in the MVP.
      </p>
    </section>
  );
}

function DecisionMetric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-xl bg-secondary/40 p-4">
      <div className="text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 font-display text-xl font-semibold">{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{detail}</div>
    </div>
  );
}
