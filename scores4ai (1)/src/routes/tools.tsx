import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { DataNotice } from "@/components/site/DataNotice";
import { ToolCard } from "@/components/site/ToolCard";
import { tools } from "@/lib/data";

export const Route = createFileRoute("/tools")({
  head: () => ({
    meta: [
      { title: "AI Tools — scores4ai" },
      {
        name: "description",
        content:
          "Compare AI tools by use case, price/value, features, source status, and transparent scoring.",
      },
    ],
  }),
  component: Tools,
});

function Tools() {
  const toolRecords = tools.filter(
    (tool) => tool.category !== "LLM" && !tool.isAgent,
  );

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-7xl px-6 py-12">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <div className="text-xs uppercase tracking-wider text-accent">
              Tool comparison records
            </div>
            <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight md:text-5xl">
              Find the right AI tool for the job
            </h1>
            <p className="mt-3 max-w-2xl text-muted-foreground">
              Browse transparent tool records with pricing status, source
              labels, and expandable score explanations instead of opaque
              rankings.
            </p>
          </div>
          <Link
            to="/rankings"
            className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-sm font-medium text-accent-foreground"
          >
            View all rankings <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="mt-8">
          <DataNotice compact />
        </div>
        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {toolRecords.map((tool, index) => (
            <ToolCard key={tool.id} tool={tool} index={index} />
          ))}
        </div>
      </main>
      <Footer />
    </div>
  );
}
