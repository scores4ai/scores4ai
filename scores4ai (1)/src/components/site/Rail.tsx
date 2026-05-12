import { ChevronLeft, ChevronRight } from "lucide-react";
import { useRef } from "react";
import type { Tool } from "@/lib/data";
import { ToolCard } from "./ToolCard";

export function Rail({
  title,
  subtitle,
  tools,
}: {
  title: string;
  subtitle?: string;
  tools: Tool[];
}) {
  const ref = useRef<HTMLDivElement>(null);
  const scroll = (dir: 1 | -1) =>
    ref.current?.scrollBy({ left: dir * 600, behavior: "smooth" });

  return (
    <section className="mt-16">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex items-end justify-between">
          <div>
            <h2 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">
              {title}
            </h2>
            {subtitle && (
              <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
            )}
          </div>
          <div className="hidden gap-2 md:flex">
            <button
              onClick={() => scroll(-1)}
              className="grid h-9 w-9 place-items-center rounded-full border border-border hover:bg-secondary"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => scroll(1)}
              className="grid h-9 w-9 place-items-center rounded-full border border-border hover:bg-secondary"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
      <div
        ref={ref}
        className="scrollbar-hide mt-6 flex gap-4 overflow-x-auto px-6 pb-4 [scroll-padding-left:1.5rem] [scroll-snap-type:x_mandatory]"
      >
        <div
          className="shrink-0"
          style={{ width: "max(0px, calc((100vw - 1280px) / 2))" }}
        />
        {tools.map((t, i) => (
          <div
            key={t.id}
            className="w-[280px] shrink-0 [scroll-snap-align:start] sm:w-[300px]"
          >
            <ToolCard tool={t} index={i} />
          </div>
        ))}
        <div className="shrink-0 pr-2" />
      </div>
    </section>
  );
}
