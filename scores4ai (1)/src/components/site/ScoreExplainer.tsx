import { scoringDimensions } from "@/lib/data-sources";

export function ScoreExplainer() {
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
        Three score types, clearly separated
      </h2>
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {scoringDimensions.map((dimension) => (
          <div key={dimension.key} className="rounded-xl bg-secondary/40 p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="font-semibold">{dimension.label}</h3>
              <span className="rounded-full bg-background/70 px-2 py-1 text-xs text-muted-foreground">
                {Math.round(dimension.weight * 100)}%
              </span>
            </div>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {dimension.description}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
