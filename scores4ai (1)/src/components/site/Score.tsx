export function ScoreMeter({
  label,
  value,
  color = "var(--accent)",
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
        <span className="font-display text-sm font-semibold">{value}</span>
      </div>
      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full rounded-full transition-all"
          style={{
            width: `${value}%`,
            background: `linear-gradient(90deg, ${color}, color-mix(in oklab, ${color} 70%, white))`,
          }}
        />
      </div>
    </div>
  );
}

export function ScoreGauge({ value, label }: { value: number; label?: string }) {
  const r = 52;
  const c = 2 * Math.PI * r;
  const off = c - (value / 100) * c;
  return (
    <div className="relative grid h-32 w-32 place-items-center">
      <svg className="absolute inset-0 -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} stroke="var(--secondary)" strokeWidth="8" fill="none" />
        <circle
          cx="60"
          cy="60"
          r={r}
          stroke="var(--accent)"
          strokeWidth="8"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={c}
          strokeDashoffset={off}
        />
      </svg>
      <div className="text-center">
        <div className="font-display text-3xl font-semibold">{value}</div>
        {label && <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>}
      </div>
    </div>
  );
}
