import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ArrowRight, Calculator, FlaskConical, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { DataNotice, LiveArchitectureCard } from "@/components/site/DataNotice";
import { Rail } from "@/components/site/Rail";
import { ScoreExplainer } from "@/components/site/ScoreExplainer";
import { LiveModelData } from "@/components/site/LiveModelData";
import { SetupChecker } from "@/components/site/SetupChecker";
import { formatUsd } from "@/lib/currency";
import { rails, tools, getTool } from "@/lib/data";
import {
  estimateModelCost,
  estimateTokensFromText,
  type PricingModel,
} from "@/lib/pricing";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "scores4ai — Prompt value comparison for AI" },
      {
        name: "description",
        content: "Enter one prompt. See which AI gives the best value.",
      },
      {
        property: "og:title",
        content: "scores4ai — Compare AI with transparency",
      },
      {
        property: "og:description",
        content:
          "Prompt Lab, pricing estimates, transparent scoring, and source labels for AI model and tool decisions.",
      },
    ],
  }),
  component: Home,
});

const pricingModels: PricingModel[] = tools.slice(0, 8).map((tool) => ({
  id: tool.id,
  name: tool.name,
  scores: tool.scores,
  inputPricePerMillion:
    tool.pricing === "Open Source" ? 0 : tool.scores.value > 90 ? 0.2 : 3,
  outputPricePerMillion:
    tool.pricing === "Open Source" ? 0 : tool.scores.value > 90 ? 0.6 : 15,
}));

function Home() {
  const featured = tools.slice(0, 6);
  const trending = rails[0].ids.map(getTool).filter(Boolean) as typeof tools;

  return (
    <div className="min-h-screen">
      <Nav />

      <section className="relative overflow-hidden">
        <div className="absolute inset-0 grid-bg" />
        <div className="relative mx-auto max-w-7xl px-6 pb-10 pt-14 md:pt-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-4xl"
          >
            <div className="inline-flex items-center gap-2 rounded-full glass px-3 py-1 text-xs text-muted-foreground">
              <Sparkles className="h-3 w-3 text-accent" aria-hidden="true" />
              Prompt-first AI value comparison
            </div>
            <h1 className="mt-6 font-display text-4xl font-semibold leading-[1.05] tracking-tight md:text-6xl">
              Enter one prompt. See which AI gives the best value.
            </h1>
            <p className="mt-5 max-w-2xl text-base text-muted-foreground md:text-lg">
              Compare models, tools, and agents by token usage, estimated cost,
              features, and real-world use case before you commit to an AI
              stack.
            </p>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <Link
                to="/prompt-lab"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-medium text-accent-foreground glow-accent"
              >
                Try Prompt Lab <FlaskConical className="h-4 w-4" />
              </Link>
              <Link
                to="/compare"
                className="inline-flex items-center justify-center gap-2 rounded-full border border-border bg-card/60 px-5 py-3 text-sm font-medium text-foreground hover:bg-secondary"
              >
                Compare Models <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/pricing-calculator"
                className="inline-flex items-center justify-center gap-2 rounded-full border border-border bg-card/60 px-5 py-3 text-sm font-medium text-foreground hover:bg-secondary"
              >
                Calculate API Cost <Calculator className="h-4 w-4" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <main className="mx-auto max-w-7xl px-6">
        <section id="prompt-lab-preview" className="pt-8">
          <PromptLabPreview />
        </section>

        <section id="pricing-preview" className="pt-8">
          <PricingPreview />
        </section>

        <section className="pt-8">
          <DataNotice />
          <div className="mt-4">
            <SetupChecker />
          </div>
        </section>

        <section id="models" className="pt-10">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <div className="text-xs uppercase tracking-wider text-accent">
                Featured model records
              </div>
              <h2 className="mt-1 font-display text-3xl font-semibold tracking-tight md:text-4xl">
                Compare records, not fake trophies
              </h2>
              <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
                Each card shows pricing status, context, source labels, and an
                expandable score explanation so demo data does not look
                verified.
              </p>
            </div>
            <Link
              to="/models"
              className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
            >
              View all models <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="mt-6">
            <LiveModelData fallbackTools={featured} limit={6} />
          </div>
        </section>

        <section className="pt-10">
          <ScoreExplainer />
        </section>

        <section id="rankings" className="pt-10">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <div className="text-xs uppercase tracking-wider text-accent">
                Rankings by use case
              </div>
              <h2 className="mt-1 font-display text-3xl font-semibold tracking-tight md:text-4xl">
                Start with a task, then inspect the sources
              </h2>
            </div>
            <Link
              to="/rankings"
              className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
            >
              Open personalized rankings <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>

      {rails.slice(0, 2).map((rail) => (
        <Rail
          key={rail.title}
          title={rail.title}
          tools={rail.ids.map(getTool).filter(Boolean) as typeof tools}
        />
      ))}

      <section className="mx-auto mt-12 max-w-7xl px-6">
        <LiveArchitectureCard />
      </section>

      <section className="mx-auto mt-12 max-w-7xl px-6">
        <div className="relative overflow-hidden rounded-3xl glass-strong p-8 md:p-12">
          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-accent/20 blur-3xl" />
          <div className="relative grid items-center gap-8 md:grid-cols-2">
            <div>
              <div className="text-xs uppercase tracking-wider text-accent">
                Next action
              </div>
              <h3 className="mt-2 font-display text-3xl font-semibold md:text-4xl">
                Need a shortlist for your workflow?
              </h3>
              <p className="mt-4 max-w-md text-muted-foreground">
                Compare the models side-by-side, inspect why each score exists,
                then estimate token spend before switching.
              </p>
              <Link
                to="/compare"
                className="mt-6 inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-sm font-medium text-accent-foreground glow-accent"
              >
                Compare models <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {trending.slice(0, 3).map((tool) => (
                <div
                  key={tool.id}
                  className="rounded-2xl glass p-4 text-center"
                >
                  <div className="mx-auto grid h-10 w-10 place-items-center rounded-lg bg-white/10 text-sm font-semibold">
                    {tool.name.slice(0, 1)}
                  </div>
                  <div className="mt-2 text-sm font-medium">{tool.name}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {tool.developer}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

function PromptLabPreview() {
  const [prompt, setPrompt] = useState(
    "Summarize the migration risk of switching a TypeScript coding agent from one model to another.",
  );
  const [selectedModelIds, setSelectedModelIds] = useState<string[]>([
    tools[0].id,
    tools[1].id,
  ]);
  const inputTokens = estimateTokensFromText(prompt);
  const outputTokens = Math.max(250, Math.round(inputTokens * 0.75));
  const selectedModels = pricingModels.filter((model) =>
    selectedModelIds.includes(model.id),
  );
  const outputCost = selectedModels.reduce(
    (sum, model) =>
      sum + (outputTokens / 1_000_000) * (model.outputPricePerMillion ?? 0),
    0,
  );

  return (
    <div className="grid gap-5 rounded-3xl glass-strong p-5 md:grid-cols-[1.2fr_0.8fr] md:p-6">
      <div>
        <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-accent">
          <FlaskConical className="h-4 w-4" aria-hidden="true" /> Prompt Lab
          preview
        </div>
        <h2 className="mt-2 font-display text-3xl font-semibold tracking-tight">
          Test one prompt across multiple models.
        </h2>
        <label className="mt-4 block text-sm">
          <span className="text-muted-foreground">Prompt</span>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            className="mt-2 min-h-28 w-full rounded-xl border border-border bg-background/60 p-4 text-sm leading-6 outline-none focus:border-accent focus:ring-2 focus:ring-accent/25"
          />
        </label>
        <div className="mt-4 flex flex-wrap gap-2">
          {pricingModels.slice(0, 4).map((model) => {
            const active = selectedModelIds.includes(model.id);
            return (
              <button
                key={model.id}
                type="button"
                onClick={() =>
                  setSelectedModelIds((current) =>
                    active
                      ? current.filter((id) => id !== model.id)
                      : [...current, model.id],
                  )
                }
                className={`rounded-full border px-3 py-1.5 text-xs transition-colors ${
                  active
                    ? "border-accent bg-accent text-accent-foreground"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                {model.name}
              </button>
            );
          })}
        </div>
      </div>
      <div className="rounded-2xl bg-background/40 p-4">
        <div className="text-xs uppercase tracking-wider text-muted-foreground">
          Estimated comparison
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 md:grid-cols-1">
          <PreviewMetric
            label="Input tokens"
            value={inputTokens.toLocaleString()}
          />
          <PreviewMetric
            label="Output tokens"
            value={outputTokens.toLocaleString()}
          />
          <PreviewMetric label="Output cost" value={formatUsd(outputCost)} />
          <PreviewMetric
            label="Models selected"
            value={selectedModels.length.toString()}
          />
        </div>
        <Link
          to="/prompt-lab"
          className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-accent px-4 py-2.5 text-sm font-medium text-accent-foreground"
        >
          Compare in Prompt Lab <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}

function PricingPreview() {
  const [promptsPerDay, setPromptsPerDay] = useState(100);
  const [avgInputTokens, setAvgInputTokens] = useState(800);
  const [avgOutputTokens, setAvgOutputTokens] = useState(300);
  const selectedModel = pricingModels[0];
  const estimate = useMemo(
    () =>
      estimateModelCost(
        { promptsPerDay, avgInputTokens, avgOutputTokens },
        selectedModel,
      ),
    [avgInputTokens, avgOutputTokens, promptsPerDay, selectedModel],
  );
  const cheapestModel = [...pricingModels].sort(
    (a, b) =>
      (a.inputPricePerMillion ?? 0) +
      (a.outputPricePerMillion ?? 0) -
      ((b.inputPricePerMillion ?? 0) + (b.outputPricePerMillion ?? 0)),
  )[0];

  return (
    <div className="grid gap-5 rounded-3xl glass p-5 md:grid-cols-[0.9fr_1.1fr] md:p-6">
      <div>
        <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-accent">
          <Calculator className="h-4 w-4" aria-hidden="true" /> Pricing
          calculator preview
        </div>
        <h2 className="mt-2 font-display text-3xl font-semibold tracking-tight">
          Estimate token spend before you pick a model.
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Inputs use transparent assumptions until live provider pricing is
          synced.
        </p>
      </div>
      <div className="grid gap-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <PreviewNumberField
            label="Prompts/day"
            value={promptsPerDay}
            onChange={setPromptsPerDay}
          />
          <PreviewNumberField
            label="Avg input tokens"
            value={avgInputTokens}
            onChange={setAvgInputTokens}
          />
          <PreviewNumberField
            label="Avg output tokens"
            value={avgOutputTokens}
            onChange={setAvgOutputTokens}
          />
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <PreviewMetric
            label="Daily cost"
            value={formatUsd(estimate.dailyCost)}
          />
          <PreviewMetric
            label="Monthly cost"
            value={formatUsd(estimate.monthlyCost)}
          />
          <PreviewMetric label="Cheapest model" value={cheapestModel.name} />
        </div>
        <Link
          to="/pricing-calculator"
          className="inline-flex items-center justify-center gap-2 rounded-full bg-foreground px-4 py-2.5 text-sm font-medium text-background hover:opacity-90"
        >
          Open full calculator <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}

function PreviewMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-secondary/40 p-3">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 font-display text-xl font-semibold">{value}</div>
    </div>
  );
}

function PreviewNumberField({
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
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-1 w-full rounded-lg border border-border bg-background/60 px-3 py-2 outline-none focus:border-accent focus:ring-2 focus:ring-accent/25"
      />
    </label>
  );
}
