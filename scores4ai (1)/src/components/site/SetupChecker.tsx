import { AlertCircle, CheckCircle2, Loader2, ServerCog } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

type SetupCheck = {
  id: string;
  label: string;
  configured: boolean;
  required: boolean;
  status: "ready" | "missing" | "optional";
  detail?: string;
};

type SetupStatus = {
  ok: boolean;
  generatedAt: string;
  summary: {
    ready: number;
    missingRequired: number;
    optionalMissing: number;
  };
  checks: SetupCheck[];
  nextActions: string[];
};

const publicChecks: SetupCheck[] = [
  {
    id: "VITE_SUPABASE_URL",
    label: "Public Supabase URL",
    configured: Boolean(import.meta.env.VITE_SUPABASE_URL),
    required: true,
    status: import.meta.env.VITE_SUPABASE_URL ? "ready" : "missing",
  },
  {
    id: "VITE_SUPABASE_ANON_KEY",
    label: "Public Supabase anon key",
    configured: Boolean(import.meta.env.VITE_SUPABASE_ANON_KEY),
    required: true,
    status: import.meta.env.VITE_SUPABASE_ANON_KEY ? "ready" : "missing",
  },
];

export function SetupChecker() {
  const [remoteStatus, setRemoteStatus] = useState<SetupStatus | undefined>();
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    fetch("/.netlify/functions/setup-status", {
      signal: controller.signal,
      cache: "no-store",
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`setup-status returned ${response.status}`);
        }
        return (await response.json()) as SetupStatus;
      })
      .then((payload) => setRemoteStatus(payload))
      .catch((caught) => {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setError(caught instanceof Error ? caught.message : "Unknown error");
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, []);

  const checks = useMemo(() => {
    const remoteChecks = remoteStatus?.checks ?? [];
    const remoteIds = new Set(remoteChecks.map((check) => check.id));
    return [
      ...publicChecks.filter((check) => !remoteIds.has(check.id)),
      ...remoteChecks,
      ...(error
        ? [
            {
              id: "setup_status_function",
              label: "Netlify setup-status function reachable",
              configured: false,
              required: true,
              status: "missing" as const,
              detail:
                "Deploy Netlify Functions or run on Netlify to verify server-only setup automatically.",
            },
          ]
        : []),
    ];
  }, [error, remoteStatus]);

  const missingRequired = checks.filter(
    (check) => check.required && !check.configured,
  );
  const optionalMissing = checks.filter(
    (check) => !check.required && !check.configured,
  );
  const readyCount = checks.filter((check) => check.configured).length;
  const ready = missingRequired.length === 0 && !error;

  return (
    <section
      className="rounded-2xl border border-border bg-card/50 p-5"
      aria-labelledby="setup-checker-title"
    >
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-accent">
            <ServerCog className="h-4 w-4" aria-hidden="true" /> Setup checker
          </div>
          <h2
            id="setup-checker-title"
            className="mt-2 font-display text-2xl font-semibold"
          >
            {ready
              ? "Live data setup is ready."
              : "Missing setup before live data is enabled."}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            This checker reads safe public config in the browser and asks a
            Netlify Function to verify server-only variables and data endpoints
            without exposing secret values.
          </p>
        </div>
        <div className="rounded-xl bg-secondary/40 px-4 py-3 text-sm">
          <div className="text-xs uppercase tracking-wider text-muted-foreground">
            Current status
          </div>
          <div className="mt-1 font-display text-2xl font-semibold">
            {loading ? "Checking…" : `${readyCount}/${checks.length} ready`}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="mt-5 flex items-center gap-2 rounded-xl bg-secondary/30 p-4 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          Checking Netlify, Supabase, and OpenRouter setup…
        </div>
      ) : (
        <>
          {missingRequired.length > 0 && (
            <div className="mt-5 rounded-xl border border-amber-400/25 bg-amber-400/10 p-4 text-sm">
              <div className="font-medium text-amber-100">
                Missing required setup
              </div>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
                {missingRequired.map((check) => (
                  <li key={check.id}>
                    <span className="text-foreground">{check.label}</span>
                    {check.detail ? ` — ${check.detail}` : null}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {checks.map((check) => (
              <div
                key={check.id}
                className="flex items-start gap-3 rounded-xl bg-secondary/30 p-3 text-sm"
              >
                {check.configured ? (
                  <CheckCircle2
                    className="mt-0.5 h-4 w-4 shrink-0 text-elite"
                    aria-hidden="true"
                  />
                ) : (
                  <AlertCircle
                    className="mt-0.5 h-4 w-4 shrink-0 text-experimental"
                    aria-hidden="true"
                  />
                )}
                <div>
                  <div className="font-medium text-foreground">
                    {check.label}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {check.configured
                      ? "Configured"
                      : check.required
                        ? "Missing"
                        : "Optional / not configured"}
                  </div>
                  {check.detail && (
                    <div className="mt-1 text-xs leading-5 text-muted-foreground">
                      {check.detail}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {optionalMissing.length > 0 && (
            <p className="mt-4 text-xs leading-5 text-muted-foreground">
              Optional missing:{" "}
              {optionalMissing.map((item) => item.label).join(", ")}. This does
              not block cached model sync, but it is required before live Prompt
              Lab API execution.
            </p>
          )}
        </>
      )}
    </section>
  );
}
