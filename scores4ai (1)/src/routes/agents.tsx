import { createFileRoute } from "@tanstack/react-router";
import { Bot, Cloud, Cpu, GitBranch, Globe, Lock } from "lucide-react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { ToolCard } from "@/components/site/ToolCard";
import { catalogTools as tools, catalogState } from "@/lib/catalog";

export const Route = createFileRoute("/agents")({
  head: () => ({
    meta: [
      { title: "AI Agents — scores4ai" },
      {
        name: "description",
        content: "Browser, coding, research, and autonomous agents — ranked.",
      },
    ],
  }),
  component: Agents,
});

function Agents() {
  const agents = tools.filter((t) => t.isAgent);
  return (
    <div className="min-h-screen">
      <Nav />
      <section className="relative overflow-hidden border-b border-border">
        <div className="absolute inset-0 grid-bg opacity-60" />
        <div className="relative mx-auto max-w-7xl px-6 py-20">
          <div className="text-xs uppercase tracking-wider text-accent">
            AI Agents
          </div>
          <h1 className="mt-2 font-display text-5xl font-semibold tracking-tight md:text-6xl">
            Agents that <span className="text-gradient">actually ship</span>
          </h1>
          <p className="mt-4 max-w-2xl text-muted-foreground">
            Browser agents, coding agents, research agents, and full autonomous
            workflows — scored on autonomy, integrations, and how often they
            break.
          </p>
        </div>
      </section>

      <div
        className="mx-auto grid max-w-7xl grid-cols-2 gap-px overflow-hidden rounded-2xl glass md:grid-cols-6 mt-12 mx-6 md:mx-auto md:px-0"
        style={{ marginInline: "1.5rem" }}
      >
        {[
          { i: Bot, l: "Autonomy" },
          { i: GitBranch, l: "Integrations" },
          { i: Cpu, l: "Local" },
          { i: Cloud, l: "Cloud" },
          { i: Lock, l: "Open source" },
          { i: Globe, l: "Browser-native" },
        ].map(({ i: Icon, l }) => (
          <div key={l} className="bg-background/30 px-4 py-5 text-center">
            <Icon className="mx-auto h-4 w-4 text-accent" />
            <div className="mt-2 text-[10px] uppercase tracking-wider text-muted-foreground">
              {l}
            </div>
          </div>
        ))}
      </div>

      <div className="mx-auto max-w-7xl px-6 py-12">
        <h2 className="font-display text-2xl font-semibold">
          Top-ranked agents
        </h2>
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {agents.map((a, i) => (
            <ToolCard key={a.id} tool={a} index={i} />
          ))}
        </div>
      </div>
      <Footer />
    </div>
  );
}
