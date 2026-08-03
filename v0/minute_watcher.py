#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright
import github_updater as updater

STATE = Path('v0/cloud_state.json')
HEARTBEAT = Path('apx/heartbeat.json')
URL = 'https://cash-pop.com/michigan/winning-numbers'
CHECKS = 50
INTERVAL = 60


def now():
    return datetime.now(timezone.utc).isoformat()


def latest_draw():
    try:
        return int(json.loads(STATE.read_text()).get('latestDraw', 0))
    except Exception:
        return 0


def run(cmd):
    return subprocess.run(cmd, check=False).returncode


def publish(draw):
    apx_ok = run(['python', 'apx/engine.py']) == 0
    evolution_ok = run(['python', 'apx/evolution.py']) == 0 if apx_ok else False
    retirement_ok = run(['python', 'apx/retirement.py']) == 0 if apx_ok else False
    ledger_ok = run(['python', 'apx/ledger.py']) == 0 if apx_ok else False
    hb = {
        'updater': 'minute-watcher',
        'lastAttemptAt': now(),
        'lastSuccessAt': now() if apx_ok else None,
        'success': apx_ok,
        'sourceSuccess': True,
        'apxSuccess': apx_ok,
        'evolutionSuccess': evolution_ok,
        'retirementSuccess': retirement_ok,
        'ledgerSuccess': ledger_ok,
        'latestDraw': draw,
        'consecutiveFailures': 0 if apx_ok else 1,
        'pollIntervalSeconds': INTERVAL,
        'architecture': 'persistent-minute-watcher-plus-five-minute-backup',
    }
    HEARTBEAT.write_text(json.dumps(hb, indent=2))
    run(['git', 'add', 'v0/cloud_state.json'])
    run(['git', 'add', '-A', 'apx'])
    if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode == 0:
        return
    run(['git', 'commit', '-m', f'Minute watcher draw {draw} {now()}'])
    for _ in range(3):
        if run(['git', 'pull', '--rebase', 'origin', 'main']) == 0 and run(['git', 'push', 'origin', 'main']) == 0:
            return
        time.sleep(4)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18 Mobile Safari/604.1',
            extra_http_headers={'Cache-Control': 'no-cache, no-store, max-age=0', 'Pragma': 'no-cache'},
        )
        for index in range(CHECKS):
            before = latest_draw()
            try:
                page.goto(URL + '?minute=' + str(time.time_ns()), wait_until='domcontentloaded', timeout=45000)
                page.wait_for_timeout(5000)
                text = page.locator('body').inner_text(timeout=15000)
                parsed = updater.parse(text)
                newest = max((int(x['draw']) for x in parsed), default=0)
                if newest > before:
                    updater.fetch_visible_text = lambda text=text: text
                    updater.main()
                    after = latest_draw()
                    if after > before:
                        publish(after)
                print(json.dumps({'check': index + 1, 'before': before, 'sourceLatest': newest, 'stored': latest_draw()}))
            except Exception as exc:
                print(json.dumps({'check': index + 1, 'error': repr(exc), 'stored': before}))
            if index < CHECKS - 1:
                time.sleep(INTERVAL)
        browser.close()


if __name__ == '__main__':
    main()
