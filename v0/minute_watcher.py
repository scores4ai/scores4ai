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


def previous_heartbeat():
    try:
        return json.loads(HEARTBEAT.read_text())
    except Exception:
        return {}


def run(cmd):
    return subprocess.run(cmd, check=False).returncode


def commit_and_push(message):
    run(['git', 'add', 'v0/cloud_state.json'])
    run(['git', 'add', '-A', 'apx'])
    if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode == 0:
        return True
    if run(['git', 'commit', '-m', message]) != 0:
        return False
    for _ in range(3):
        if run(['git', 'pull', '--rebase', 'origin', 'main']) == 0 and run(['git', 'push', 'origin', 'main']) == 0:
            return True
        time.sleep(4)
    return False


def write_heartbeat(source_ok, draw, error=None, apx_ok=None):
    old = previous_heartbeat()
    failures = 0 if source_ok else int(old.get('consecutiveFailures', 0)) + 1
    successful_at = now() if source_ok else old.get('lastSuccessAt')
    hb = {
        'updater': 'minute-watcher',
        'lastAttemptAt': now(),
        'lastSuccessAt': successful_at,
        'success': bool(source_ok and (apx_ok is not False)),
        'sourceSuccess': bool(source_ok),
        'apxSuccess': apx_ok,
        'latestDraw': draw,
        'consecutiveFailures': failures,
        'pollIntervalSeconds': INTERVAL,
        'architecture': 'persistent-minute-watcher-plus-five-minute-backup',
    }
    if error:
        hb['lastError'] = str(error)[:500]
    HEARTBEAT.write_text(json.dumps(hb, indent=2))


def publish(draw):
    apx_ok = run(['python', 'apx/engine.py']) == 0
    evolution_ok = run(['python', 'apx/evolution.py']) == 0 if apx_ok else False
    retirement_ok = run(['python', 'apx/retirement.py']) == 0 if apx_ok else False
    ledger_ok = run(['python', 'apx/ledger.py']) == 0 if apx_ok else False
    write_heartbeat(True, draw, apx_ok=apx_ok)
    hb = previous_heartbeat()
    hb.update({
        'evolutionSuccess': evolution_ok,
        'retirementSuccess': retirement_ok,
        'ledgerSuccess': ledger_ok,
    })
    HEARTBEAT.write_text(json.dumps(hb, indent=2))
    commit_and_push(f'Minute watcher draw {draw} {now()}')


def new_page(browser):
    return browser.new_page(
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18 Mobile Safari/604.1',
        extra_http_headers={'Cache-Control': 'no-cache, no-store, max-age=0', 'Pragma': 'no-cache'},
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = new_page(browser)
        for index in range(CHECKS):
            before = latest_draw()
            try:
                page.goto(URL + '?minute=' + str(time.time_ns()), wait_until='domcontentloaded', timeout=45000)
                page.wait_for_timeout(5000)
                text = page.locator('body').inner_text(timeout=15000)
                parsed = updater.parse(text)
                newest = max((int(x['draw']) for x in parsed), default=0)
                if newest <= 0:
                    raise RuntimeError('Source returned no parseable Cash Pop draws')
                if newest > before:
                    updater.fetch_visible_text = lambda text=text: text
                    updater.main()
                    after = latest_draw()
                    if after > before:
                        publish(after)
                    else:
                        raise RuntimeError(f'Source showed draw {newest}, but stored state did not advance')
                else:
                    write_heartbeat(True, before, apx_ok=True)
                    commit_and_push(f'Minute watcher heartbeat {before} {now()}')
                print(json.dumps({'check': index + 1, 'before': before, 'sourceLatest': newest, 'stored': latest_draw()}))
            except Exception as exc:
                write_heartbeat(False, before, error=repr(exc), apx_ok=False)
                commit_and_push(f'Minute watcher failure {before} {now()}')
                print(json.dumps({'check': index + 1, 'error': repr(exc), 'stored': before}))
                try:
                    page.close()
                except Exception:
                    pass
                page = new_page(browser)
            if index < CHECKS - 1:
                time.sleep(INTERVAL)
        browser.close()


if __name__ == '__main__':
    main()
