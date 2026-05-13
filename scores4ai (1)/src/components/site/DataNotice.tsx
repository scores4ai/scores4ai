import { DatabaseZap, Info } from "lucide-react";
import {
  MODEL_FRESHNESS_HOURS,
  PRICING_FRESHNESS_HOURS,
  dataSourceCopy,
} from "@/lib/data-sources";

export function DataNotice({ compact = false }: { compact?: boolean }) {
  return (
    <aside
      className={`rounded-2xl border border-accent/25 bg-accent/10 ${compact ? "p-4" : "p-5"}`}
      aria-label="Data source notice"
    >
      <div className="flex items-start gap-3">
        <Info
          className="mt-0.5 h-4 w-4 shrink-0 text-accent"
          aria-hidden="true"
        />
        <div>
          <div className="text-sm font-semibold text-foreground">
            Demo data is shown until live OpenRouter/Supabase sync is enabled.
          </div>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Honest source labels remain visible on records, but demo values are
            not presented as verified rankings.
          </p>
          <div className="mt-3 flex flex-wrap gap-2 text-[11px] uppercase tracking-wider text-muted-foreground">
            <span className="rounded-full border border-border px-2 py-1">
              Model refresh: {MODEL_FRESHNESS_HOURS}h
            </span>
            <span className="rounded-full border border-border px-2 py-1">
              Pricing refresh: {PRICING_FRESHNESS_HOURS}h
            </span>
            <span className="rounded-full border border-border px-2 py-1">
              Supabase cache ready
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}

export function LiveArchitectureCard() {
  return (
    <div className="rounded-2xl glass p-5">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <DatabaseZap className="h-4 w-4 text-accent" aria-hidden="true" />{" "}
        Real-time data pipeline
      </div>
      <ol className="mt-4 space-y-3 text-sm text-muted-foreground">
        <li>
          <span className="text-foreground">1.</span> Fetch OpenRouter model
          metadata and prices from{" "}
          <code className="rounded bg-secondary px-1">/api/v1/models</code>.
        </li>
        <li>
          <span className="text-foreground">2.</span> Cache raw responses and
          normalized pricing in Supabase.
        </li>
        <li>
          <span className="text-foreground">3.</span> Merge benchmark snapshots,
          community ratings, and vetted programmer reviews.
        </li>
        <li>
          <span className="text-foreground">4.</span> Show cached data with
          freshness labels when upstream APIs fail.
        </li>
      </ol>
    </div>
  );
}
