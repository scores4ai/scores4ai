import { Link, useLocation } from "@tanstack/react-router";
import { Search, Sparkles } from "lucide-react";

export function Nav() {
  const { pathname } = useLocation();
  const link = (to: string, label: string) => (
    <Link
      to={to}
      className={`text-sm transition-colors ${
        pathname === to ? "text-foreground" : "text-muted-foreground hover:text-foreground"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <header className="sticky top-0 z-50 glass-strong">
      <div className="mx-auto flex max-w-7xl items-center gap-8 px-6 py-4">
        <Link to="/" className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-accent-foreground">
            <Sparkles className="h-4 w-4" />
          </div>
          <span className="font-display text-lg font-semibold tracking-tight">
            scores<span className="text-accent">4</span>ai
          </span>
        </Link>
        <nav className="hidden items-center gap-6 md:flex">
          {link("/", "Discover")}
          {link("/rankings", "Rankings")}
          {link("/agents", "Agents")}
          {link("/compare", "Compare")}
          {link("/community", "Community")}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-border bg-card/40 px-3 py-1.5 text-sm text-muted-foreground sm:flex">
            <Search className="h-4 w-4" />
            <span>Search 1,200+ AI tools</span>
            <kbd className="ml-2 rounded border border-border px-1.5 py-0.5 text-[10px]">⌘K</kbd>
          </div>
          <button className="rounded-full bg-foreground px-4 py-2 text-sm font-medium text-background hover:opacity-90">
            Sign in
          </button>
        </div>
      </div>
    </header>
  );
}
