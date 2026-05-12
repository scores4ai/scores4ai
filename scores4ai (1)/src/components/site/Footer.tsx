export function Footer() {
  return (
    <footer className="mt-32 border-t border-border">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-16 md:grid-cols-4">
        <div>
          <div className="font-display text-lg font-semibold">
            scores<span className="text-accent">4</span>ai
          </div>
          <p className="mt-3 max-w-xs text-sm text-muted-foreground">
            The internet's AI ranking engine. Built by people who actually use AI.
          </p>
        </div>
        {[
          { h: "Discover", l: ["Rankings", "Agents", "Open Source", "Trending"] },
          { h: "Community", l: ["Reviews", "Leaderboard", "Discussions", "Collections"] },
          { h: "Company", l: ["About", "Methodology", "Careers", "Press"] },
        ].map((c) => (
          <div key={c.h}>
            <div className="text-sm font-semibold">{c.h}</div>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              {c.l.map((x) => (
                <li key={x} className="hover:text-foreground">{x}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-border py-6 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} scores4ai — Independent. Opinionated. Receipt-driven.
      </div>
    </footer>
  );
}
