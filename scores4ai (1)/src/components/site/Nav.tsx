import { Link, useLocation } from "@tanstack/react-router";
import { Menu, Search, Sparkles } from "lucide-react";
import { useState } from "react";

const navItems = [
  ["/", "Discover"],
  ["/rankings", "Rankings"],
  ["/agents", "Agents"],
  ["/compare", "Compare"],
  ["/community", "Community"],
] as const;

export function Nav() {
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  const link = (to: string, label: string) => (
    <Link
      to={to}
      onClick={() => setOpen(false)}
      className={`rounded-lg px-2 py-1.5 text-sm transition-colors ${
        pathname === to
          ? "text-foreground"
          : "text-muted-foreground hover:text-foreground"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6">
        <Link
          to="/"
          className="flex items-center gap-2"
          aria-label="Scores4AI home"
        >
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-accent-foreground">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
          </div>
          <span className="font-display text-lg font-semibold tracking-tight">
            scores<span className="text-accent">4</span>ai
          </span>
        </Link>
        <nav
          className="hidden items-center gap-2 md:flex"
          aria-label="Primary navigation"
        >
          {navItems.map(([to, label]) => link(to, label))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <form
            action="/rankings"
            method="get"
            className="hidden items-center gap-2 rounded-full border border-border bg-card/40 px-3 py-1.5 text-sm text-muted-foreground sm:flex"
            role="search"
          >
            <Search className="h-4 w-4" aria-hidden="true" />
            <label className="sr-only" htmlFor="site-search">
              Search tools
            </label>
            <input
              id="site-search"
              name="q"
              className="w-36 bg-transparent outline-none placeholder:text-muted-foreground lg:w-52"
              placeholder="Search AI tools"
            />
          </form>
          <Link
            to="/rankings"
            className="hidden rounded-full bg-foreground px-4 py-2 text-sm font-medium text-background hover:opacity-90 sm:inline-flex"
          >
            View rankings
          </Link>
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            className="grid h-10 w-10 place-items-center rounded-full border border-border md:hidden"
            aria-expanded={open}
            aria-controls="mobile-nav"
          >
            <Menu className="h-4 w-4" aria-hidden="true" />
            <span className="sr-only">Toggle menu</span>
          </button>
        </div>
      </div>
      {open && (
        <nav
          id="mobile-nav"
          className="border-t border-border px-4 py-3 md:hidden"
          aria-label="Mobile navigation"
        >
          <div className="grid gap-1">
            {navItems.map(([to, label]) => link(to, label))}
          </div>
        </nav>
      )}
    </header>
  );
}
