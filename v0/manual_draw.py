#!/usr/bin/env python3
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import github_updater as updater

STATE = Path('v0/cloud_state.json')
HEARTBEAT = Path('apx/heartbeat.json')


def now():
    return datetime.now(timezone.utc).isoformat()


def run(*cmd):
    subprocess.run(list(cmd), check=True)


def main():
    draw = int(os.environ['MANUAL_DRAW'])
    number = int(os.environ['MANUAL_NUMBER'])
    entered_by = os.environ.get('MANUAL_ACTOR', 'unknown')

    if not 1 <= number <= 15:
        raise SystemExit('Winning number must be from 1 through 15.')

    state = json.loads(STATE.read_text())
    latest = int(state.get('latestDraw', 0))
    existing = {int(x['draw']): int(x['number']) for x in state.get('draws', [])}

    if draw in existing:
        if existing[draw] == number:
            print(f'Draw #{draw} already exists with number {number}; nothing to change.')
            return
        raise SystemExit(f'Draw #{draw} already exists with a different number.')
    if draw != latest + 1:
        raise SystemExit(f'Manual draw must be exactly #{latest + 1}; received #{draw}.')

    local = datetime.now().astimezone()
    date_text = local.strftime('%A, %B %d, %Y').replace(' 0', ' ')
    time_text = local.strftime('%I:%M %p').lstrip('0')
    synthetic = f'{date_text}\n{number}\n#{draw}\n{time_text}\n'

    updater.fetch_visible_text = lambda: synthetic
    updater.main()

    for script in ['apx/engine.py', 'apx/evolution.py', 'apx/retirement.py', 'apx/ledger.py']:
        run('python', script)

    heartbeat = {
        'updater': 'manual-entry',
        'lastAttemptAt': now(),
        'lastSuccessAt': now(),
        'success': True,
        'sourceSuccess': False,
        'drawAdvanced': True,
        'sourceUrl': None,
        'sourceLatestDraw': draw,
        'latestDraw': draw,
        'sourceGap': 0,
        'consecutiveFailures': 0,
        'manualEntry': True,
        'enteredBy': entered_by,
        'lastError': None,
        'liveDefinition': 'Manual entry accepted after strict sequence and range validation',
        'architecture': 'automatic watcher plus owner-authorized manual fallback'
    }
    HEARTBEAT.write_text(json.dumps(heartbeat, indent=2))
    print(json.dumps({'accepted': True, 'draw': draw, 'number': number, 'enteredBy': entered_by}))


if __name__ == '__main__':
    main()
