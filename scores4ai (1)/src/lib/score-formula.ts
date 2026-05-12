export type ScoreComponents = {
  community?: number;
  expert?: number;
  performance?: number;
  value?: number;
  trust?: number;
  freshness?: number;
};

export const DEFAULT_SCORE_WEIGHTS: Required<ScoreComponents> = {
  community: 0.2,
  expert: 0.25,
  performance: 0.15,
  value: 0.15,
  trust: 0.15,
  freshness: 0.1,
};

export const SCORE_FORMULA_DESCRIPTION =
  "Overall = community×20% + expert×25% + performance×15% + value×15% + trust×15% + freshness×10%. Each component is scored 0-100.";

function clampScore(value = 0) {
  return Math.min(100, Math.max(0, value));
}

export function calculateTransparentScore(
  components: ScoreComponents,
  weights: Required<ScoreComponents> = DEFAULT_SCORE_WEIGHTS,
): number {
  const score = Object.entries(weights).reduce((sum, [key, weight]) => {
    return sum + clampScore(components[key as keyof ScoreComponents]) * weight;
  }, 0);

  return Number(score.toFixed(2));
}

export function explainTransparentScore(components: ScoreComponents) {
  const overall = calculateTransparentScore(components);
  return {
    overall,
    description: SCORE_FORMULA_DESCRIPTION,
    weights: DEFAULT_SCORE_WEIGHTS,
    components: {
      community: clampScore(components.community),
      expert: clampScore(components.expert),
      performance: clampScore(components.performance),
      value: clampScore(components.value),
      trust: clampScore(components.trust),
      freshness: clampScore(components.freshness),
    },
  };
}
