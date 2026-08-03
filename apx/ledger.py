#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

STATE = Path('apx/state.json')
SOURCE = Path('v0/cloud_state.json')


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    state = json.loads(STATE.read_text())
    source = json.loads(SOURCE.read_text())
    draws = {int(row['draw']): row for row in source.get('draws', [])}

    old_ledger = state.get('drawLedger') or {}
    old_records = {int(row['draw']): row for row in old_ledger.get('records', [])}
    live = {int(row['draw']): row for row in state.get('liveHistory', []) if row.get('type') == 'apx_live_forward'}

    records = []
    for draw_id in sorted(draws):
        official = draws[draw_id]
        prediction = live.get(draw_id)
        previous = old_records.get(draw_id, {})

        if prediction:
            status = 'valid_prediction'
            reason = None
            counts = True
            top5 = [int(x) for x in prediction.get('top5', [])]
            actual = int(official['number'])
            result = 'SUCCESS' if actual in top5 else 'MISS'
            predicted_at = prediction.get('predictedAt')
            fingerprint = prediction.get('predictionFingerprint')
            model_count = prediction.get('modelCount')
        else:
            status = 'unpredicted_draw'
            counts = False
            top5 = []
            actual = int(official['number'])
            result = 'NOT_SCORED'
            predicted_at = None
            fingerprint = None
            model_count = None
            reason = previous.get('missingReason') or 'No immutable APX prediction was stored before this result was ingested.'

        records.append({
            'draw': draw_id,
            'officialNumber': actual,
            'officialDate': official.get('date'),
            'officialTime': official.get('time'),
            'officialSource': official.get('source') or source.get('source'),
            'predictionStatus': status,
            'prediction': top5,
            'predictedAt': predicted_at,
            'fingerprint': fingerprint,
            'activeModelCount': model_count,
            'result': result,
            'countsTowardAccuracy': counts,
            'missingReason': reason,
            'auditedAt': now(),
        })

    valid = sum(1 for row in records if row['countsTowardAccuracy'])
    missing = len(records) - valid
    recent = records[-100:]
    recent_valid = sum(1 for row in recent if row['countsTowardAccuracy'])
    coverage = valid / len(records) if records else 0.0
    recent_coverage = recent_valid / len(recent) if recent else 0.0

    state['drawLedger'] = {
        'version': 1,
        'updatedAt': now(),
        'officialDrawsRecorded': len(records),
        'validPredictions': valid,
        'unpredictedDraws': missing,
        'predictionCoverage': coverage,
        'recent100Coverage': recent_coverage,
        'missingDataBias': 'LOW' if recent_coverage >= 0.95 else ('MODERATE' if recent_coverage >= 0.80 else 'HIGH'),
        'rule': 'Every ingested official draw receives a permanent record. Only immutable predictions stored before the result count toward model accuracy.',
        'records': records[-2000:],
    }
    state['version'] = 'APX Phase 1.7'
    STATE.write_text(json.dumps(state, indent=2))
    print(json.dumps({
        'officialDraws': len(records),
        'validPredictions': valid,
        'unpredictedDraws': missing,
        'coverage': coverage,
        'recent100Coverage': recent_coverage,
    }))


if __name__ == '__main__':
    main()
