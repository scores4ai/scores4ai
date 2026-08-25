import { Link } from "@tanstack/react-router";
import { TrendingDown, TrendingUp } from "lucide-react";
import type { Tool } from "@/lib/data";
import { verdictColor } from "@/lib/data";
import { dataSourceCopy } from "@/lib/data-sources";
import { motion } from "framer-motion";

type ToolCardProps = {
  tool: Tool;
  index?: number;
  displayScore?: number;
  displayScoreLabel?: string;
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
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.4, delay: Math.min(index, 8) * 0.03 }}
    >
      <Link
        to="/tool/$id"
        params={{ id: tool.id }}
        className="group relative block h-full overflow-hidden rounded-2xl glass p-5 transition-all hover:-translate-y-0.5 hover:border-white/15"
      >
        <div className="flex items-start justify-between">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-white/15 to-white/5 text-base font-semibold">
            {tool.name.slice(0, 1)}
          </div>
          <div className="flex flex-col items-end gap-1">
            <span className="rounded-full border border-accent/25 bg-accent/10 px-2 py-0.5 text-[10px] uppercase tracking-wider text-accent">
              {dataSourceCopy[tool.sourceStatus].label}
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
          <div className="flex items-center gap-2">
            <h3 className="font-display text-lg font-semibold">{tool.name}</h3>
            <span className="text-xs text-muted-foreground">
              · {tool.developer}
            </span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
            {tool.tagline}
          </p>
        </div>
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
              {trendUp ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              {Math.abs(tool.trend)}%
            </span>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-2 rounded-xl bg-secondary/30 p-2 text-center text-[10px] text-muted-foreground">
          <div>
            <span className="block font-display text-sm text-foreground">
              {displayScore}
            </span>
            {compactScoreLabel}
          </div>
          <div>
            <span className="block font-display text-sm text-foreground">
              {tool.scores.community}
            </span>
            Community
          </div>
          <div>
            <span className="block font-display text-sm text-foreground">
              {tool.scores.programmer}
            </span>
            Programmer
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-1.5">
          {tool.tags.slice(0, 3).map((t) => (
            <span
              key={t}
              className="rounded-md bg-secondary px-2 py-0.5 text-[10px] text-muted-foreground"
            >
              {t}
            </span>
          ))}
          <span className="rounded-md border border-border px-2 py-0.5 text-[10px] text-muted-foreground">
            {tool.evidenceCount > 0
              ? `${tool.evidenceCount} evidence links`
              : "Evidence pending"}
          </span>
        </div>
      </Link>
    </motion.div>
  );
}
