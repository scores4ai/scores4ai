import { useMemo, useState } from "react";

const templates = {
  compare:
    "Compare {{tool_a}} and {{tool_b}} for {{use_case}}. Include strengths, risks, cost assumptions, and a final recommendation.",
  score:
    "Score {{tool}} for {{use_case}} using capability, reliability, speed, value, privacy, and hallucination resistance. Return evidence and confidence.",
  agent:
    "Design an agent workflow for {{use_case}}. List required tools, failure modes, review checkpoints, and escalation criteria.",
};

export function PromptLab() {
  const [template, setTemplate] = useState<keyof typeof templates>("compare");
  const [useCase, setUseCase] = useState("production TypeScript coding");
  const [toolA, setToolA] = useState("Claude");
  const [toolB, setToolB] = useState("GPT");

  const prompt = useMemo(
    () =>
      templates[template]
        .replaceAll("{{tool_a}}", toolA)
        .replaceAll("{{tool_b}}", toolB)
        .replaceAll("{{tool}}", toolA)
        .replaceAll("{{use_case}}", useCase),
    [template, toolA, toolB, useCase],
  );

  return (
    <section
      className="rounded-2xl glass p-5"
      aria-labelledby="prompt-lab-title"
    >
      <div className="text-xs uppercase tracking-wider text-accent">
        Prompt Lab
      </div>
      <h2
        id="prompt-lab-title"
        className="mt-1 font-display text-2xl font-semibold"
      >
        Generate repeatable evaluation prompts
      </h2>
      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <label className="text-sm">
          <span className="text-muted-foreground">Template</span>
          <select
            value={template}
            onChange={(event) =>
              setTemplate(event.target.value as keyof typeof templates)
            }
            className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2"
          >
            <option value="compare">Comparison</option>
            <option value="score">Score audit</option>
            <option value="agent">Agent workflow</option>
          </select>
        </label>
        <TextInput label="Primary tool" value={toolA} onChange={setToolA} />
        <TextInput label="Secondary tool" value={toolB} onChange={setToolB} />
      </div>
      <TextInput
        label="Use case"
        value={useCase}
        onChange={setUseCase}
        className="mt-4"
      />
      <textarea
        readOnly
        value={prompt}
        className="mt-4 min-h-32 w-full rounded-xl border border-border bg-background/60 p-4 text-sm leading-6 text-foreground"
        aria-label="Generated prompt"
      />
    </section>
  );
}

function TextInput({
  label,
  value,
  onChange,
  className = "",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  className?: string;
}) {
  return (
    <label className={`block text-sm ${className}`}>
      <span className="text-muted-foreground">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 outline-none focus:border-accent focus:ring-2 focus:ring-accent/25"
      />
    </label>
  );
}
