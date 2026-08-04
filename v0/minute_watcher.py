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
URLS = [
    'https://cash-pop.com/',
    'https://cash-pop.com/michigan/winning-numbers',
    'https://cash-pop.com/michigan/past-winning-numbers',
]
INTERVAL = 0
CHECKS = 1


def now():
    return datetime.now(timezone.utc).isoformat()


def latest_draw():
    try:
        return int(json.loads(STATE.read_text()).get('latestDraw', 0))
    except Exception:
        return 0


def load_heartbeat():
    try:
        return json.loads(HEARTBEAT.read_text())
    except Exception:
        return {}


def run(cmd):
    return subprocess.run(cmd, check=False).returncode


def push_visible_branch(message):
    run(['git', 'fetch', 'origin', 'gh-pages'])
    run(['git', 'worktree', 'remove', '--force', '/tmp/gh-pages'])
    if run(['git', 'worktree', 'add', '--force', '/tmp/gh-pages', 'origin/gh-pages']) != 0:
        return False
    try:
        Path('/tmp/gh-pages/state.json').write_text(Path('apx/state.json').read_text())
        Path('/tmp/gh-pages/heartbeat.json').write_text(Path('apx/heartbeat.json').read_text())
        Path('/tmp/gh-pages/v0').mkdir(parents=True, exist_ok=True)
        Path('/tmp/gh-pages/v0/cloud_state.json').write_text(STATE.read_text())
        run(['git', '-C', '/tmp/gh-pages', 'config', 'user.name', 'cash-pop-live-bot'])
        run(['git', '-C', '/tmp/gh-pages', 'config', 'user.email', 'cash-pop-live-bot@users.noreply.github.com'])
        run(['git', '-C', '/tmp/gh-pages', 'add', 'state.json', 'heartbeat.json', 'v0/cloud_state.json'])
        if subprocess.run(['git', '-C', '/tmp/gh-pages', 'diff', '--cached', '--quiet']).returncode == 0:
            return True
        if run(['git', '-C', '/tmp/gh-pages', 'commit', '-m', message]) != 0:
            return False
        for _ in range(4):
            if run(['git', '-C', '/tmp/gh-pages', 'pull', '--rebase', 'origin', 'gh-pages']) == 0 and run(['git', '-C', '/tmp/gh-pages', 'push', 'origin', 'HEAD:gh-pages']) == 0:
                return True
            time.sleep(2)
        return False
    finally:
        run(['git', 'worktree', 'remove', '--force', '/tmp/gh-pages'])


def commit_and_push(message):
    run(['git', 'add', 'v0/cloud_state.json'])
    run(['git', 'add', '-A', 'apx'])
    if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode != 0:
        if run(['git', 'commit', '-m', message]) != 0:
            return False
        for _ in range(5):
            if run(['git', 'pull', '--rebase', 'origin', 'main']) == 0 and run(['git', 'push', 'origin', 'main']) == 0:
                break
            time.sleep(2)
        else:
            return False
    return push_visible_branch(message)


def write_heartbeat(source_ok, source_url, source_latest, stored_draw, advanced, error=None):
    old = load_heartbeat()
    hb = {
        'updater': 'persistent-live-watcher',
        'lastAttemptAt': now(),
        'lastSuccessAt': now() if source_ok else old.get('lastSuccessAt'),
        'success': bool(source_ok),
        'sourceSuccess': bool(source_ok),
        'drawAdvanced': bool(advanced),
        'sourceUrl': source_url,
        'sourceLatestDraw': int(source_latest or 0),
        'latestDraw': int(stored_draw),
        'sourceGap': max(0, int(source_latest or 0) - int(stored_draw)),
        'consecutiveFailures': 0 if source_ok else int(old.get('consecutiveFailures', 0)) + 1,
        'pollIntervalSeconds': INTERVAL,
        'lastError': error,
        'liveDefinition': 'Persistent browser polling with matching source and stored draw',
        'architecture': 'warm-browser-persistent-loop-plus-same-origin-pages-state',
    }
    HEARTBEAT.write_text(json.dumps(hb, indent=2))
    commit_and_push(f'Cash Pop live check {stored_draw} {now()}')


def publish(draw, source_url, source_latest):
    apx_ok = run(['python', 'apx/engine.py']) == 0
    evolution_ok = run(['python', 'apx/evolution.py']) == 0 if apx_ok else False
    retirement_ok = run(['python', 'apx/retirement.py']) == 0 if apx_ok else False
    ledger_ok = run(['python', 'apx/ledger.py']) == 0 if apx_ok else False
    hb = {
        'updater': 'persistent-live-watcher',
        'lastAttemptAt': now(),
        'lastSuccessAt': now(),
        'success': bool(apx_ok),
        'sourceSuccess': True,
        'drawAdvanced': True,
        'sourceUrl': source_url,
        'sourceLatestDraw': int(source_latest),
        'latestDraw': int(draw),
        'sourceGap': max(0, int(source_latest) - int(draw)),
        'apxSuccess': apx_ok,
        'evolutionSuccess': evolution_ok,
        'retirementSuccess': retirement_ok,
        'ledgerSuccess': ledger_ok,
        'consecutiveFailures': 0,
        'pollIntervalSeconds': INTERVAL,
        'lastError': None,
        'liveDefinition': 'Persistent browser polling with matching source and stored draw',
        'architecture': 'warm-browser-persistent-loop-plus-same-origin-pages-state',
    }
    HEARTBEAT.write_text(json.dumps(hb, indent=2))
    commit_and_push(f'Cash Pop draw {draw} {now()}')


def new_page(browser):
    return browser.new_page(
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18 Mobile Safari/604.1',
        extra_http_headers={'Cache-Control': 'no-cache, no-store, max-age=0', 'Pragma': 'no-cache'},
    )


def fetch_best(page):
    errors = []
    best = None
    for url in URLS:
        try:
            page.goto(url + ('&' if '?' in url else '?') + 'live=' + str(time.time_ns()), wait_until='domcontentloaded', timeout=45000)
            page.wait_for_timeout(1200)
            text = page.locator('body').inner_text(timeout=15000)
            parsed = updater.parse(text)
            newest = max((int(x['draw']) for x in parsed), default=0)
            if newest and (best is None or newest > best['newest']):
                best = {'url': url, 'text': text, 'newest': newest}
        except Exception as exc:
            errors.append(f'{url}: {exc!r}')
    return best, ('; '.join(errors) if not best else None)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = new_page(browser)
        try:
            for index in range(CHECKS):
                before = latest_draw()
                try:
                    best, error = fetch_best(page)
                    if not best:
                        write_heartbeat(False, None, 0, before, False, error or 'No parseable source')
                        page.close()
                        page = new_page(browser)
                    else:
                        newest = best['newest']
                        if newest > before:
                            updater.fetch_visible_text = lambda text=best['text']: text
                            updater.main()
                            after = latest_draw()
                            if after > before:
                                publish(after, best['url'], newest)
                            else:
                                write_heartbeat(True, best['url'], newest, after, False, 'Source was newer but state did not advance')
                        else:
                            write_heartbeat(True, best['url'], newest, before, False, 'No newer draw available from checked sources')
                except Exception as exc:
                    write_heartbeat(False, None, 0, before, False, repr(exc))
                    try:
                        page.close()
                    except Exception:
                        pass
                    page = new_page(browser)
                if index < CHECKS - 1:
                    time.sleep(INTERVAL)
        finally:
            browser.close()


if __name__ == '__main__':
    main()
