#!/usr/bin/env python3
import json
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright
import github_updater as updater

STATE = Path('v0/cloud_state.json')
HEARTBEAT = Path('apx/heartbeat.json')
URLS = [
    'https://cash-pop.com/michigan/winning-numbers',
    'https://cash-pop.com/michigan/past-winning-numbers',
]
CHECKS = 50
INTERVAL = 60


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


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=False).returncode


def sync_pages_branch():
    """Copy the current live JSON into gh-pages during this same workflow run."""
    temp_dir = Path(tempfile.mkdtemp(prefix='apx-gh-pages-'))
    try:
        run(['git', 'fetch', 'origin', 'gh-pages'])
        if run(['git', 'worktree', 'add', '--force', str(temp_dir), 'gh-pages']) != 0:
            return False

        (temp_dir / 'apx').mkdir(parents=True, exist_ok=True)
        for source, destinations in (
            (Path('apx/state.json'), [temp_dir / 'state.json', temp_dir / 'apx/state.json']),
            (Path('apx/heartbeat.json'), [temp_dir / 'heartbeat.json', temp_dir / 'apx/heartbeat.json']),
        ):
            if not source.exists():
                continue
            for destination in destinations:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

        run(['git', 'add', 'state.json', 'heartbeat.json', 'apx/state.json', 'apx/heartbeat.json'], cwd=temp_dir)
        if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=temp_dir).returncode == 0:
            return True
        if run(['git', 'commit', '-m', f'Publish APX live state {latest_draw()} {now()}'], cwd=temp_dir) != 0:
            return False
        for _ in range(3):
            if run(['git', 'pull', '--rebase', 'origin', 'gh-pages'], cwd=temp_dir) == 0 and run(['git', 'push', 'origin', 'gh-pages'], cwd=temp_dir) == 0:
                return True
            time.sleep(3)
        return False
    finally:
        run(['git', 'worktree', 'remove', '--force', str(temp_dir)])
        shutil.rmtree(temp_dir, ignore_errors=True)


def commit_and_push(message):
    run(['git', 'add', 'v0/cloud_state.json'])
    run(['git', 'add', '-A', 'apx'])
    changed = subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode != 0
    if changed:
        if run(['git', 'commit', '-m', message]) != 0:
            return False
        pushed = False
        for _ in range(3):
            if run(['git', 'pull', '--rebase', 'origin', 'main']) == 0 and run(['git', 'push', 'origin', 'main']) == 0:
                pushed = True
                break
            time.sleep(4)
        if not pushed:
            return False
    return sync_pages_branch()


def write_heartbeat(*, source_ok, source_url, source_latest, stored_draw, advanced, error=None):
    old = load_heartbeat()
    failures = 0 if source_ok else int(old.get('consecutiveFailures', 0)) + 1
    hb = {
        'updater': 'minute-watcher',
        'lastAttemptAt': now(),
        'lastSuccessAt': now() if advanced else old.get('lastSuccessAt'),
        'success': bool(advanced),
        'sourceSuccess': bool(source_ok),
        'drawAdvanced': bool(advanced),
        'sourceUrl': source_url,
        'sourceLatestDraw': int(source_latest or 0),
        'latestDraw': int(stored_draw),
        'sourceGap': max(0, int(source_latest or 0) - int(stored_draw)),
        'consecutiveFailures': failures,
        'pollIntervalSeconds': INTERVAL,
        'lastError': error,
        'liveDefinition': 'A newer source draw was parsed and committed',
        'architecture': 'same-run-main-and-gh-pages-publisher',
    }
    HEARTBEAT.write_text(json.dumps(hb, indent=2))
    commit_and_push(f"Cash Pop heartbeat {stored_draw} {now()}")


def publish(draw, source_url, source_latest):
    apx_ok = run(['python', 'apx/engine.py']) == 0
    evolution_ok = run(['python', 'apx/evolution.py']) == 0 if apx_ok else False
    retirement_ok = run(['python', 'apx/retirement.py']) == 0 if apx_ok else False
    ledger_ok = run(['python', 'apx/ledger.py']) == 0 if apx_ok else False
    hb = {
        'updater': 'minute-watcher',
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
        'liveDefinition': 'A newer source draw was parsed and committed',
        'architecture': 'same-run-main-and-gh-pages-publisher',
    }
    HEARTBEAT.write_text(json.dumps(hb, indent=2))
    commit_and_push(f'Minute watcher draw {draw} {now()}')


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
            page.goto(url + '?minute=' + str(time.time_ns()), wait_until='domcontentloaded', timeout=45000)
            page.wait_for_timeout(5000)
            text = page.locator('body').inner_text(timeout=15000)
            parsed = updater.parse(text)
            newest = max((int(x['draw']) for x in parsed), default=0)
            if newest and (best is None or newest > best['newest']):
                best = {'url': url, 'text': text, 'parsed': parsed, 'newest': newest}
        except Exception as exc:
            errors.append(f'{url}: {exc!r}')
    if best:
        return best, None
    return None, '; '.join(errors) or 'No source produced parseable draw rows'


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = new_page(browser)
        for index in range(CHECKS):
            before = latest_draw()
            try:
                best, error = fetch_best(page)
                if not best:
                    write_heartbeat(source_ok=False, source_url=None, source_latest=0,
                                    stored_draw=before, advanced=False, error=error)
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
                            write_heartbeat(source_ok=True, source_url=best['url'], source_latest=newest,
                                            stored_draw=after, advanced=False,
                                            error='Source was newer but cloud_state did not advance')
                    else:
                        write_heartbeat(source_ok=True, source_url=best['url'], source_latest=newest,
                                        stored_draw=before, advanced=False,
                                        error='Source returned no draw newer than stored state')
                print(json.dumps({'check': index + 1, 'before': before,
                                  'sourceLatest': best['newest'] if best else 0,
                                  'stored': latest_draw(), 'source': best['url'] if best else None}))
            except Exception as exc:
                write_heartbeat(source_ok=False, source_url=None, source_latest=0,
                                stored_draw=before, advanced=False, error=repr(exc))
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
