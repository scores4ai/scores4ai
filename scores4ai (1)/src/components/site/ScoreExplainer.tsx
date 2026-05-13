import { useMemo, useState } from "react";
import { tools } from "@/lib/data";
import {
  defaultScoreWeights,
  normalizeWeights,
  transparentScore,
  type ScoreWeight,
} from "@/lib/scoring";

export function ScoreExplainer() {
  const [weights, setWeights] = useState<ScoreWeight[]>(defaultScoreWeights);
  const normalized = useMemo(() => normalizeWeights(weights), [weights]);
  const example = useMemo(
    () => transparentScore(tools[0], normalized),
    [normalized],
  );

  function updateWeight(key: ScoreWeight["key"], value: number) {
    setWeights((current) =>
      current.map((item) =>
        item.key === key ? { ...item, weight: value / 100 } : item,
      ),
    );
  }

  return (
    <section
      className="rounded-2xl glass p-5"
      aria-labelledby="score-methodology-title"
    >
      <div className="text-xs uppercase tracking-wider text-accent">
        Transparent scoring
      </div>
      <h2
        id="score-methodology-title"
        className="mt-1 font-display text-2xl font-semibold"
      >
        Formula, weights, sources, confidence
      </h2>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">
        Formula: <span className="text-foreground">{example.formula}</span> No
        hidden formulas: every category below shows its weighting and input.
      </p>
      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {normalized.map((dimension) => (
          <label
            key={dimension.key}
            className="rounded-xl bg-secondary/40 p-4 text-sm"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="font-semibold">{dimension.label}</span>
              <span className="rounded-full bg-background/70 px-2 py-1 text-xs text-muted-foreground">
                {Math.round(dimension.weight * 100)}%
              </span>
            </div>
            <input
              className="mt-3 w-full accent-[hsl(var(--accent))]"
              type="range"
              min="0"
              max="60"
              value={Math.round(
                weights.find((w) => w.key === dimension.key)!.weight * 100,
              )}
              onChange={(event) =>
                updateWeight(dimension.key, Number(event.target.value))
              }
              aria-label={`${dimension.label} weight`}
            />
            <p className="mt-2 leading-6 text-muted-foreground">
              Input: {dimension.formulaInput}.
            </p>
          </label>
        ))}
      </div>
      <div className="mt-5 rounded-xl border border-border bg-background/40 p-4 text-sm text-muted-foreground">
        <div className="font-semibold text-foreground">
          Example score audit: {tools[0].name} → {example.score}/100
        </div>
        <div className="mt-2 grid gap-2 md:grid-cols-3">
          <span>Source: {example.source}</span>
          <span>Confidence: {example.confidence}</span>
          <span>Updated: {example.updatedDate}</span>
        </div>
      </div>
    </section>
  );
}
