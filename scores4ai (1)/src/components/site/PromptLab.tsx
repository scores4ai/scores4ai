import { useMemo, useState } from "react";
import { catalogTools as tools } from "@/lib/catalog";
import { formatUsd } from "@/lib/currency";
import { estimateTokensFromText } from "@/lib/pricing";

const modelDefaults = tools.slice(0, 6).map((tool) => ({
  id: tool.id,
  name: tool.name,
  contextWindow: tool.contextWindow ?? "Unknown",
  speed: tool.scores.speed,
  formatting: tool.scores.ease,
  reasoning: tool.scores.intelligence,
  hallucinationRisk: 100 - tool.scores.hallucination,
  citations: tool.tags.includes("research") || tool.tags.includes("search"),
  inputPrice:
    tool.pricing === "Open Source" ? 0 : tool.scores.value > 90 ? 0.2 : 3,
  outputPrice:
    tool.pricing === "Open Source" ? 0 : tool.scores.value > 90 ? 0.6 : 15,
}));

export function PromptLab() {
  const [prompt, setPrompt] = useState(
    "Compare the top risks of adopting this model for a production TypeScript coding agent. Include evidence, cost assumptions, and a final recommendation.",
  );
  const [selected, setSelected] = useState<string[]>(
    modelDefaults.slice(0, 3).map((model) => model.id),
  );
  const [expectedOutputTokens, setExpectedOutputTokens] = useState(800);

  const inputTokens = useMemo(() => estimateTokensFromText(prompt), [prompt]);
  const selectedModels = modelDefaults.filter((model) =>
    selected.includes(model.id),
  );

  function toggleModel(id: string) {
    setSelected((current) =>
      current.includes(id)
        ? current.filter((modelId) => modelId !== id)
        : [...current, id],
    );
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
            Compare one prompt across multiple models
          </h2>
        </div>
        <span className="rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-xs uppercase tracking-wider text-amber-200">
          Estimated MVP results
        </span>
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
          <span className="text-muted-foreground">Estimated output tokens</span>
          <input
            type="number"
            min="1"
            value={expectedOutputTokens}
            onChange={(event) =>
              setExpectedOutputTokens(Number(event.target.value))
            }
            className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 outline-none focus:border-accent focus:ring-2 focus:ring-accent/25"
          />
        </label>
      </div>

      <div className="mt-5 overflow-x-auto rounded-xl border border-border">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-secondary/60 text-xs uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Tokens</th>
              <th className="px-4 py-3">Estimated cost</th>
              <th className="px-4 py-3">Context</th>
              <th className="px-4 py-3">Speed</th>
              <th className="px-4 py-3">Quality signals</th>
            </tr>
          </thead>
          <tbody>
            {selectedModels.map((model) => {
              const cost =
                (inputTokens / 1_000_000) * model.inputPrice +
                (expectedOutputTokens / 1_000_000) * model.outputPrice;
              return (
                <tr key={model.id} className="border-t border-border">
                  <td className="px-4 py-3 font-medium">{model.name}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {inputTokens.toLocaleString()} in /{" "}
                    {expectedOutputTokens.toLocaleString()} out
                  </td>
                  <td className="px-4 py-3">{formatUsd(cost)}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {model.contextWindow}
                  </td>
                  <td className="px-4 py-3">{model.speed}/100</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    Formatting {model.formatting}/100 · Reasoning{" "}
                    {model.reasoning}/100 · Hallucination risk{" "}
                    {model.hallucinationRisk}/100 · Citations{" "}
                    {model.citations ? "Likely" : "Not verified"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs leading-5 text-muted-foreground">
        Live API Result will appear when server-side OpenRouter execution is
        enabled. Until then, Prompt Lab uses transparent token and price
        estimates only.
      </p>
    </section>
  );
}
