import { createFileRoute } from "@tanstack/react-router";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { DataNotice } from "@/components/site/DataNotice";
import { PricingCalculator } from "@/components/site/PricingCalculator";

export const Route = createFileRoute("/pricing-calculator")({
  head: () => ({
    meta: [
      { title: "AI Pricing Calculator — scores4ai" },
      {
        name: "description",
        content:
          "Estimate daily, monthly, yearly, and per-task AI API costs across model options.",
      },
    ],
  }),
  component: PricingCalculatorRoute,
});

function PricingCalculatorRoute() {
  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-7xl px-6 py-12">
        <div className="mb-8">
          <div className="text-xs uppercase tracking-wider text-accent">
            Pricing Calculator
          </div>
          <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight md:text-5xl">
            Estimate API spend before you switch models
          </h1>
          <p className="mt-3 max-w-2xl text-muted-foreground">
            Enter expected prompts and token volume to compare estimated daily,
            monthly, yearly, and per-task costs.
          </p>
        </div>
        <DataNotice compact />
        <div className="mt-8">
          <PricingCalculator />
        </div>
      </main>
      <Footer />
    </div>
  );
}
