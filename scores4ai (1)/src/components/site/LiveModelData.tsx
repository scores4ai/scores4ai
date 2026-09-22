import { AlertCircle, CheckCircle2, Loader2, Wifi } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { formatUsd } from "@/lib/currency";
import type { Tool } from "@/lib/data";
import { ToolCard } from "./ToolCard";

type LiveModelRecord = {
  id: string;
  name: string;
  provider: string;
  description: string;
  contextWindow: number | null;
  inputPricePerMillion: number;
  outputPricePerMillion: number;
  inputModalities: string[];
  outputModalities: string[];
  supportedParameters: string[];
  sourceStatus: "live" | "cached" | "estimated" | "demo";
  sourceLabel: string;
  lastSyncedAt: string | null;
};

type OpenRouterModelsPayload = {
  dataMode: "live" | "cached" | "demo";
  generatedAt: string;
  records: LiveModelRecord[];
  checks: {
    openRouter: {
      keyDetected: boolean;
      ok: boolean;
      status: string;
      detail: string;
    };
    supabase: {
      configured: boolean;
      ok: boolean;
      detail: string;
    };
  };
  nextActions: string[];
};

type LiveModelDataProps = {
  fallbackTools: Tool[];
  limit?: number;
  showStatus?: boolean;
};

function liveRecordToTool(record: LiveModelRecord): Tool {
  const free =
    record.inputPricePerMillion === 0 && record.outputPricePerMillion === 0;
  const contextScore = record.contextWindow
    ? record.contextWindow >= 200_000
      ? 92
      : record.contextWindow >= 100_000
        ? 84
        : 74
    : 65;
  const valueScore = free ? 100 : record.inputPricePerMillion <= 1 ? 92 : 78;

  return {
    id: record.id.replaceAll("/", "--"),
    name: record.name,
    developer: record.provider,
    category: "LLM",
    tags: [
      ...record.inputModalities,
      ...record.outputModalities,
      ...record.supportedParameters.slice(0, 2),
    ].filter(Boolean),
    pricing: free ? "Free" : "Paid",
    released: "Live metadata",
    tagline: record.description,
    description: record.description,
    website: `https://openrouter.ai/${record.id}`,
    trend: 0,
    verdict: "Experimental",
    sourceStatus: record.sourceStatus,
    evidenceCount: record.sourceStatus === "live" ? 1 : 0,
    scores: {
      overall: Math.round((contextScore + valueScore) / 2),
      ai: Math.round((contextScore + valueScore) / 2),
      community: 50,
      programmer: contextScore,
      speed: 70,
      intelligence: contextScore,
      ease: record.supportedParameters.length > 0 ? 82 : 72,
      value: valueScore,
      hallucination: 70,
      privacy: 50,
      creativity: 70,
    },
    contextWindow: record.contextWindow
      ? `${record.contextWindow.toLocaleString()} tokens`
      : undefined,
    modality: [...record.inputModalities, ...record.outputModalities],
    openRouterId: record.id,
    inputPricePerMillion: record.inputPricePerMillion,
    outputPricePerMillion: record.outputPricePerMillion,
    priceSourceLabel: record.sourceLabel,
    lastVerified: record.lastSyncedAt ?? "Live OpenRouter response",
  };
}

export function LiveModelData({
  fallbackTools,
  limit = 6,
  showStatus = true,
}: LiveModelDataProps) {
  const [payload, setPayload] = useState<OpenRouterModelsPayload | undefined>();
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    fetch("/.netlify/functions/openrouter-models", {
      signal: controller.signal,
      cache: "no-store",
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`openrouter-models returned ${response.status}`);
        }
        return (await response.json()) as OpenRouterModelsPayload;
      })
      .then((result) => setPayload(result))
      .catch((caught) => {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setError(caught instanceof Error ? caught.message : "Unknown error");
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, []);

  const liveTools = useMemo(
    () => (payload?.records ?? []).slice(0, limit).map(liveRecordToTool),
    [limit, payload?.records],
  );
  const usingLiveOrCache = Boolean(
    payload && payload.dataMode !== "demo" && liveTools.length > 0,
  );
  const toolsToRender = usingLiveOrCache
    ? liveTools
    : fallbackTools.slice(0, limit);
  const dataMode = usingLiveOrCache ? payload?.dataMode : "demo";

  return (
    <div className="space-y-4">
      {showStatus && (
        <DataStatusPanel
          payload={payload}
          error={error}
          loading={loading}
          dataMode={dataMode ?? "demo"}
        />
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {toolsToRender.map((tool, index) => (
          <ToolCard
            key={tool.id}
            tool={tool}
            index={index}
            linkToRecord={!usingLiveOrCache}
          />
        ))}
      </div>
    </div>
  );
}

function DataStatusPanel({
  payload,
  error,
  loading,
  dataMode,
}: {
  payload?: OpenRouterModelsPayload;
  error?: string;
  loading: boolean;
  dataMode: "live" | "cached" | "demo";
}) {
  const openRouter = payload?.checks.openRouter;
  const supabase = payload?.checks.supabase;
  const modeLabel =
    dataMode === "live"
      ? "Using Live OpenRouter data"
      : dataMode === "cached"
        ? "Using Supabase cached data"
        : "Using Demo fallback data";

  return (
    <aside className="rounded-2xl border border-border bg-card/50 p-4">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-accent">
            <Wifi className="h-4 w-4" aria-hidden="true" /> Live data status
          </div>
          <h3 className="mt-1 font-display text-xl font-semibold">
            {modeLabel}
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Live labels are only shown when the server function successfully
            fetches OpenRouter. Otherwise the app falls back to cached or demo
            records.
          </p>
        </div>
        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />{" "}
            Checking…
          </div>
        )}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <StatusPill
          label="OpenRouter key"
          ok={Boolean(openRouter?.keyDetected)}
          pending={loading}
          value={openRouter?.keyDetected ? "Detected" : "Missing"}
        />
        <StatusPill
          label="OpenRouter fetch"
          ok={Boolean(openRouter?.ok)}
          pending={loading}
          value={openRouter?.ok ? "Success" : "Failure"}
        />
        <StatusPill
          label="Supabase"
          ok={Boolean(supabase?.ok)}
          pending={loading}
          value={supabase?.ok ? "Connected" : "Missing"}
        />
        <StatusPill
          label="Data mode"
          ok={dataMode !== "demo"}
          pending={loading}
          value={dataMode.toUpperCase()}
        />
      </div>

      {!loading && (error || openRouter?.detail || supabase?.detail) && (
        <div className="mt-4 space-y-2 rounded-xl bg-secondary/30 p-3 text-xs leading-5 text-muted-foreground">
          {error && (
            <div>
              <span className="text-foreground">Function:</span> {error}. Deploy
              the Netlify function before live data can be verified.
            </div>
          )}
          {openRouter?.detail && (
            <div>
              <span className="text-foreground">OpenRouter:</span>{" "}
              {openRouter.detail}
            </div>
          )}
          {supabase?.detail && (
            <div>
              <span className="text-foreground">Supabase:</span>{" "}
              {supabase.detail}
            </div>
          )}
          {payload?.nextActions?.map((action) => (
            <div key={action}>Next: {action}</div>
          ))}
        </div>
      )}
    </aside>
  );
}

function StatusPill({
  label,
  value,
  ok,
  pending,
}: {
  label: string;
  value: string;
  ok: boolean;
  pending: boolean;
}) {
  return (
    <div className="rounded-xl bg-secondary/30 p-3 text-sm">
      <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-muted-foreground">
        {pending ? (
          <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
        ) : ok ? (
          <CheckCircle2 className="h-3 w-3 text-elite" aria-hidden="true" />
        ) : (
          <AlertCircle
            className="h-3 w-3 text-experimental"
            aria-hidden="true"
          />
        )}
        {label}
      </div>
      <div className="mt-1 font-medium text-foreground">
        {pending ? "Checking" : value}
      </div>
    </div>
  );
}
