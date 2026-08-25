import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { DataNotice } from "@/components/site/DataNotice";
import { LiveModelData } from "@/components/site/LiveModelData";
import { tools } from "@/lib/data";

export const Route = createFileRoute("/models")({
  head: () => ({
    meta: [
      { title: "AI Models — scores4ai" },
      {
        name: "description",
        content:
          "Compare AI models by transparent scores, context window, pricing status, and source labels.",
      },
    ],
  }),
  component: Models,
});

function Models() {
  const models = tools.filter((tool) => tool.category === "LLM");

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-7xl px-6 py-12">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <div className="text-xs uppercase tracking-wider text-accent">
              Model comparison records
            </div>
            <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight md:text-5xl">
              Compare AI models by cost, context, and fit
            </h1>
            <p className="mt-3 max-w-2xl text-muted-foreground">
              Model cards show demo/estimated values until OpenRouter and
              Supabase sync are enabled, with every score explaining its formula
              and confidence.
            </p>
          </div>
          <Link
            to="/compare"
            className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-sm font-medium text-accent-foreground"
          >
            Compare selected models <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="mt-8">
          <DataNotice compact />
        </div>
        <div className="mt-8">
          <LiveModelData fallbackTools={models} limit={12} />
        </div>
      </main>
      <Footer />
    </div>
  );
}
