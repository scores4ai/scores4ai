import { createFileRoute } from "@tanstack/react-router";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { DataNotice } from "@/components/site/DataNotice";
import { PromptLab } from "@/components/site/PromptLab";

export const Route = createFileRoute("/prompt-lab")({
  head: () => ({
    meta: [
      { title: "Prompt Lab — scores4ai" },
      {
        name: "description",
        content:
          "Test one prompt across multiple AI models with transparent estimated tokens, costs, and quality signals.",
      },
    ],
  }),
  component: PromptLabRoute,
});

function PromptLabRoute() {
  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-7xl px-6 py-12">
        <div className="mb-8">
          <div className="text-xs uppercase tracking-wider text-accent">
            Prompt Lab
          </div>
          <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight md:text-5xl">
            Test one prompt across multiple models
          </h1>
          <p className="mt-3 max-w-2xl text-muted-foreground">
            MVP results are estimated until live API execution is enabled
            server-side.
          </p>
        </div>
        <DataNotice compact />
        <div className="mt-8">
          <PromptLab />
        </div>
      </main>
      <Footer />
    </div>
  );
}
