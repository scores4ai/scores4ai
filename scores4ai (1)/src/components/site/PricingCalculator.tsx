import { useMemo, useState } from "react";
import { formatUsd } from "@/lib/openrouter";

const presets = [
  { name: "Light chat", input: 60_000, output: 20_000 },
  { name: "Agent workflow", input: 2_000_000, output: 600_000 },
  { name: "Codebase audit", input: 8_000_000, output: 1_200_000 },
];

export function PricingCalculator() {
  const [inputTokens, setInputTokens] = useState(1_000_000);
  const [outputTokens, setOutputTokens] = useState(250_000);
  const [inputPrice, setInputPrice] = useState(3);
  const [outputPrice, setOutputPrice] = useState(15);

  const total = useMemo(
    () =>
      (inputTokens / 1_000_000) * inputPrice +
      (outputTokens / 1_000_000) * outputPrice,
    [inputTokens, outputTokens, inputPrice, outputPrice],
  );

  return (
    <section
      className="rounded-2xl glass p-5"
      aria-labelledby="pricing-calculator-title"
    >
      <div className="text-xs uppercase tracking-wider text-accent">
        Pricing calculator
      </div>
      <h2
        id="pricing-calculator-title"
        className="mt-1 font-display text-2xl font-semibold"
      >
        Estimate model spend before you switch
      </h2>
      <div className="mt-5 flex flex-wrap gap-2">
        {presets.map((preset) => (
          <button
            key={preset.name}
            type="button"
            onClick={() => {
              setInputTokens(preset.input);
              setOutputTokens(preset.output);
            }}
            className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground hover:border-accent hover:text-foreground"
          >
            {preset.name}
          </button>
        ))}
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <NumberField
          label="Input tokens / month"
          value={inputTokens}
          onChange={setInputTokens}
        />
        <NumberField
          label="Output tokens / month"
          value={outputTokens}
          onChange={setOutputTokens}
        />
        <NumberField
          label="Input $ / 1M tokens"
          value={inputPrice}
          onChange={setInputPrice}
          step="0.1"
        />
        <NumberField
          label="Output $ / 1M tokens"
          value={outputPrice}
          onChange={setOutputPrice}
          step="0.1"
        />
      </div>
      <div className="mt-5 rounded-xl bg-secondary/40 p-4">
        <div className="text-xs uppercase tracking-wider text-muted-foreground">
          Estimated monthly cost
        </div>
        <div className="mt-1 font-display text-4xl font-semibold">
          {formatUsd(total)}
        </div>
      </div>
    </section>
  );
}

function NumberField({
  label,
  value,
  onChange,
  step = "1000",
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  step?: string;
}) {
  return (
    <label className="text-sm">
      <span className="text-muted-foreground">{label}</span>
      <input
        type="number"
        min="0"
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-foreground outline-none focus:border-accent focus:ring-2 focus:ring-accent/25"
      />
    </label>
  );
}
