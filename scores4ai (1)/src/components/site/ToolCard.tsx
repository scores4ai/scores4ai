import { Link } from "@tanstack/react-router";
import {
  ArrowRight,
  ExternalLink,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import type { Tool } from "@/lib/data";
import { verdictColor } from "@/lib/data";
import { dataSourceCopy } from "@/lib/data-sources";
import { formatUsd } from "@/lib/currency";
import { transparentScore } from "@/lib/scoring";
import { motion } from "framer-motion";

type ScoreDetails = ReturnType<typeof transparentScore>;

type ToolCardProps = {
  tool: Tool;
  index?: number;
  displayScore?: number;
  displayScoreLabel?: string;
  scoreDetails?: ScoreDetails;
  linkToRecord?: boolean;
};

function estimatedTokenPrices(tool: Tool) {
  if (
    tool.inputPricePerMillion !== undefined ||
    tool.outputPricePerMillion !== undefined
  ) {
    return {
      input: tool.inputPricePerMillion ?? 0,
      output: tool.outputPricePerMillion ?? 0,
      label:
        tool.priceSourceLabel ??
        (tool.openRouterId ? "OpenRouter" : "Supabase Cache"),
    };
  }
  if (tool.pricing === "Open Source") {
    return { input: 0, output: 0, label: "Open source" };
  }
  return {
    input: tool.scores.value > 90 ? 0.2 : 3,
    output: tool.scores.value > 90 ? 0.6 : 15,
    label: "Estimated",
  };
}

export function ToolCard({
  tool,
  index = 0,
  displayScore,
  displayScoreLabel = "AI score",
  scoreDetails,
  linkToRecord = true,
}: ToolCardProps) {
  const details = scoreDetails ?? transparentScore(tool);
  const score = displayScore ?? details.score;
  const trendUp = tool.trend >= 0;
  const compactScoreLabel =
    displayScoreLabel === "AI score" ? "Score" : "Weighted";
  const tokenPrices = estimatedTokenPrices(tool);
  const sourceLabel =
    tool.sourceStatus === "live"
      ? "OpenRouter"
      : tool.sourceStatus === "cached"
        ? "Supabase Cache"
        : dataSourceCopy[tool.sourceStatus].label.replace(" seed data", "");

};

export function ToolCard({
  tool,
  index = 0,
  displayScore = tool.scores.ai,
  displayScoreLabel = "AI score",
}: ToolCardProps) {
  const trendUp = tool.trend >= 0;
  const compactScoreLabel =
    displayScoreLabel === "AI score" ? "AI" : "Weighted";
  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.4, delay: Math.min(index, 8) * 0.03 }}
      className="group relative flex h-full flex-col overflow-hidden rounded-2xl glass p-5 transition-all hover:-translate-y-0.5 hover:border-white/15"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-white/15 to-white/5 text-base font-semibold">
          {tool.name.slice(0, 1)}
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="rounded-full border border-border bg-secondary/40 px-2 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
            Source: {sourceLabel}
          </span>
          <div
            className="rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider"
            style={{
              color: verdictColor[tool.verdict],
              background: `color-mix(in oklab, ${verdictColor[tool.verdict]} 15%, transparent)`,
              border: `1px solid color-mix(in oklab, ${verdictColor[tool.verdict]} 30%, transparent)`,
            }}
          >
            {tool.verdict}
          </div>
        </div>
      </div>

      <div className="mt-4">
        <div className="flex flex-wrap items-center gap-2">
          {linkToRecord ? (
            <Link
              to="/tool/$id"
              params={{ id: tool.id }}
              className="font-display text-lg font-semibold hover:text-accent"
        <div className="mt-5 flex items-end justify-between">
          <div>
            <div className="font-display text-3xl font-semibold tracking-tight">
              {displayScore}
            </div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
              {displayScoreLabel}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <span className="rounded-full border border-border px-2 py-0.5 text-[10px] text-muted-foreground">
              {tool.pricing}
            </span>
            <span
              className={`flex items-center gap-1 text-xs ${
                trendUp ? "text-elite" : "text-broken"
              }`}
            >
              {tool.name}
            </Link>
          ) : (
            <a
              href={tool.website}
              target="_blank"
              rel="noreferrer"
              className="font-display text-lg font-semibold hover:text-accent"
            >
              {tool.name}
            </a>
          )}
          <span className="text-xs text-muted-foreground">
            · {tool.developer}
          </span>
        </div>
        <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
          {tool.tagline}
        </p>
      </div>

      <div className="mt-5 flex items-end justify-between gap-4">
        <div>
          <div className="font-display text-3xl font-semibold tracking-tight">
            {score}
        <div className="mt-4 grid grid-cols-3 gap-2 rounded-xl bg-secondary/30 p-2 text-center text-[10px] text-muted-foreground">
          <div>
            <span className="block font-display text-sm text-foreground">
              {displayScore}
            </span>
            {compactScoreLabel}
          </div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
            {displayScoreLabel}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <span className="rounded-full border border-border px-2 py-0.5 text-[10px] text-muted-foreground">
            {tool.pricing}
          </span>
          <span
            className={`flex items-center gap-1 text-xs ${
              trendUp ? "text-elite" : "text-broken"
            }`}
          >
            {trendUp ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {Math.abs(tool.trend)}%
          </span>
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-2 rounded-xl bg-secondary/30 p-2 text-[10px] text-muted-foreground sm:grid-cols-4">
        <div>
          <dt className="uppercase tracking-wider">Context</dt>
          <dd className="mt-1 font-display text-sm text-foreground">
            {tool.contextWindow ?? "TBD"}
          </dd>
        </div>
        <div>
          <dt className="uppercase tracking-wider">Input / 1M</dt>
          <dd className="mt-1 font-display text-sm text-foreground">
            {formatUsd(tokenPrices.input)}
          </dd>
        </div>
        <div>
          <dt className="uppercase tracking-wider">Output / 1M</dt>
          <dd className="mt-1 font-display text-sm text-foreground">
            {formatUsd(tokenPrices.output)}
          </dd>
        </div>
        <div>
          <dt className="uppercase tracking-wider">Price source</dt>
          <dd className="mt-1 font-display text-sm text-foreground">
            {tokenPrices.label}
          </dd>
        </div>
      </dl>

      <details className="mt-4 rounded-xl border border-border bg-background/30 p-3 text-sm">
        <summary className="cursor-pointer list-none text-xs font-medium uppercase tracking-wider text-accent">
          Why this score?
        </summary>
        <div className="mt-3 space-y-3 text-xs leading-5 text-muted-foreground">
          <p>{details.formula}</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {details.contributions.map((item) => (
              <div key={item.key} className="rounded-lg bg-secondary/40 p-2">
                <div className="flex justify-between gap-2 text-foreground">
                  <span>{item.label}</span>
                  <span>{Math.round(item.weight * 100)}%</span>
                </div>
                <div>Input score: {item.input}</div>
              </div>
            ))}
          </div>
          <dl className="grid gap-2 sm:grid-cols-2">
            <div>
              <dt className="text-foreground">Source</dt>
              <dd>{details.source}</dd>
            </div>
            <div>
              <dt className="text-foreground">Confidence</dt>
              <dd>{details.confidence}</dd>
            </div>
            <div>
              <dt className="text-foreground">Last updated</dt>
              <dd>{details.updatedDate}</dd>
            </div>
            <div>
              <dt className="text-foreground">Displayed as</dt>
              <dd>{compactScoreLabel} score record</dd>
            </div>
          </dl>
        </div>
      </details>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          {tool.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="rounded-md bg-secondary px-2 py-0.5 text-[10px] text-muted-foreground"
            >
              {tag}
            </span>
          ))}
        </div>
        {linkToRecord ? (
          <Link
            to="/tool/$id"
            params={{ id: tool.id }}
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            View record <ArrowRight className="h-3 w-3" />
          </Link>
        ) : (
          <a
            href={tool.website}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            Open source <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
    </motion.article>
  );
}
