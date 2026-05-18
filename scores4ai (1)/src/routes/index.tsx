import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Calculator,
  FlaskConical,
  Search,
  Sparkles,
  Zap,
} from "lucide-react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { DataNotice, LiveArchitectureCard } from "@/components/site/DataNotice";
import { Rail } from "@/components/site/Rail";
import { ScoreExplainer } from "@/components/site/ScoreExplainer";
import { ToolCard } from "@/components/site/ToolCard";
import { rails, tools, getTool } from "@/lib/data";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "scores4ai — The internet's AI ranking engine" },
      {
        name: "description",
        content:
          "Discover the best AI models, tools, and agents. OpenRouter metadata, transparent benchmark scoring, community ratings, and vetted programmer reviews.",
      },
      { property: "og:title", content: "scores4ai — Discover the best AI" },
      {
        property: "og:description",
        content:
          "Stop wasting time testing bad AI tools. See what actually works.",
      },
    ],
  }),
  component: Home,
});

function Home() {
  const featured = tools.slice(0, 6);
  const trending = rails[0].ids.map(getTool).filter(Boolean) as typeof tools;

  return (
    <div className="min-h-screen">
      <Nav />

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 grid-bg" />
        <div className="relative mx-auto max-w-7xl px-6 pb-20 pt-24 md:pt-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mx-auto max-w-4xl text-center"
          >
            <div className="mx-auto inline-flex items-center gap-2 rounded-full glass px-3 py-1 text-xs text-muted-foreground">
              <Sparkles className="h-3 w-3 text-accent" />
              Compare AI by task, price, context, and evidence
            </div>
            <h1 className="mt-6 font-display text-5xl font-semibold leading-[1.05] tracking-tight md:text-7xl">
              Pick the right AI model <br />
              <span className="text-gradient">before you spend tokens</span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-base text-muted-foreground md:text-lg">
              Scores4AI turns messy model choice into a decision workflow:
              search models, compare one prompt across providers, estimate API
              cost, and see exactly which data is live, cached, or estimated.
            </p>

            <div className="mx-auto mt-8 flex max-w-2xl flex-col justify-center gap-3 sm:flex-row">
              <Link
                to="/compare"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-medium text-accent-foreground glow-accent"
              >
                <FlaskConical className="h-4 w-4" /> Run Prompt Lab
              </Link>
              <Link
                to="/rankings"
                search={{ q: "coding" }}
                className="inline-flex items-center justify-center gap-2 rounded-full border border-border px-5 py-3 text-sm font-medium text-foreground hover:bg-secondary"
              >
                <Calculator className="h-4 w-4" /> Compare token costs
              </Link>
            </div>

            <form
              action="/rankings"
              method="get"
              className="mx-auto mt-8 flex max-w-xl items-center gap-2 rounded-full glass-strong p-2 pl-5"
              role="search"
            >
              <Search className="h-4 w-4 text-muted-foreground" />
              <label className="sr-only" htmlFor="hero-search">
                Search AI models, tools, and agents
              </label>
              <input
                id="hero-search"
                name="q"
                placeholder="Search coding, research, agents, open source..."
                className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              />
              <button
                type="submit"
                className="rounded-full bg-foreground px-4 py-2 text-sm font-medium text-background"
              >
                Search
              </button>
            </form>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-2 text-xs text-muted-foreground">
              {[
                "coding",
                "research",
                "agents",
                "open source",
                "low cost",
                "privacy",
              ].map((t) => (
                <a
                  key={t}
                  href={`/rankings?q=${encodeURIComponent(t)}`}
                  className="rounded-full border border-border px-2.5 py-1 hover:bg-secondary"
                >
                  {t}
                </a>
              ))}
            </div>
          </motion.div>

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {[
              [
                "1",
                "Search by job",
                "Find models and tools for coding, research, agents, privacy, or low-cost workloads.",
              ],
              [
                "2",
                "Compare a prompt",
                "Prompt Lab estimates tokens, context fit, price, speed, and hallucination risk before any API call.",
              ],
              [
                "3",
                "Trust the label",
                "Every score declares whether it is live, cached, estimated, or demo seed data.",
              ],
            ].map(([n, title, body]) => (
              <div key={title} className="rounded-2xl glass p-5 text-left">
                <div className="grid h-8 w-8 place-items-center rounded-full bg-accent text-sm font-semibold text-accent-foreground">
                  {n}
                </div>
                <div className="mt-4 font-display text-xl font-semibold">
                  {title}
                </div>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {body}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-6">
            <DataNotice />
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 pt-12">
        <ScoreExplainer />
      </section>

      {/* FEATURED GRID */}
      <section className="mx-auto max-w-7xl px-6 pt-12">
        <div className="flex items-end justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider text-accent">
              Decision starters
            </div>
            <h2 className="mt-1 font-display text-3xl font-semibold tracking-tight md:text-4xl">
              Start with transparent comparison cards
            </h2>
          </div>
          <Link
            to="/rankings"
            className="hidden items-center gap-1 text-sm text-muted-foreground hover:text-foreground md:flex"
          >
            See full rankings <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {featured.map((t, i) => (
            <ToolCard key={t.id} tool={t} index={i} />
          ))}
        </div>
      </section>

      {/* RAILS */}
      {rails.map((r) => (
        <Rail
          key={r.title}
          title={r.title}
          tools={r.ids.map(getTool).filter(Boolean) as typeof tools}
        />
      ))}

      <section className="mx-auto mt-16 max-w-7xl px-6">
        <LiveArchitectureCard />
      </section>

      {/* COMPARE CTA */}
      <section className="mx-auto mt-24 max-w-7xl px-6">
        <div className="relative overflow-hidden rounded-3xl glass-strong p-10 md:p-16">
          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-accent/20 blur-3xl" />
          <div className="absolute -left-20 -bottom-20 h-64 w-64 rounded-full bg-accent/10 blur-3xl" />
          <div className="relative grid items-center gap-10 md:grid-cols-2">
            <div>
              <div className="text-xs uppercase tracking-wider text-accent">
                Side by side
              </div>
              <h3 className="mt-2 font-display text-3xl font-semibold md:text-4xl">
                ChatGPT vs Claude vs Gemini.
                <br />
                <span className="text-muted-foreground">
                  Settle it with data.
                </span>
              </h3>
              <p className="mt-4 max-w-md text-muted-foreground">
                Reasoning, coding, writing, speed, context, hallucinations, and
                pricing — visualized with labeled sources and estimates.
              </p>
              <Link
                to="/compare"
                className="mt-6 inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-sm font-medium text-accent-foreground glow-accent"
              >
                Compare models <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {trending.slice(0, 3).map((t) => (
                <div key={t.id} className="rounded-2xl glass p-4 text-center">
                  <div className="mx-auto grid h-10 w-10 place-items-center rounded-lg bg-white/10 text-sm font-semibold">
                    {t.name.slice(0, 1)}
                  </div>
                  <div className="mt-2 text-sm font-medium">{t.name}</div>
                  <div className="mt-2 font-display text-2xl font-semibold">
                    {t.scores.ai}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* MANIFESTO */}
      <section className="mx-auto mt-24 max-w-4xl px-6 text-center">
        <Zap className="mx-auto h-6 w-6 text-accent" />
        <h3 className="mt-4 font-display text-3xl font-semibold tracking-tight md:text-5xl">
          See what actually works.
        </h3>
        <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
          Built by people who actually use AI. Independent. Opinionated.
          Receipts included.
        </p>
      </section>

      <Footer />
    </div>
  );
}
