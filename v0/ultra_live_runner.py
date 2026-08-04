#!/usr/bin/env python3
"""Run the existing validated watcher at low latency without commit spam."""
import time
import minute_watcher as watcher

# Keep two overlapping GitHub Actions runners warm. Each checks sources every
# five seconds for about 55 minutes instead of repeatedly starting browsers.
watcher.INTERVAL = 5
watcher.CHECKS = 660

_original_heartbeat = watcher.write_heartbeat
_last_heartbeat_push = 0.0


def throttled_heartbeat(*, source_ok, source_url, source_latest, stored_draw,
                         advanced, error=None):
    """Publish idle health at most once/minute; publish failures immediately.

    A newly advanced draw is handled by watcher.publish(), so this function is
    mainly for no-change and error checks. Avoiding a Git commit every five
    seconds keeps the repository and Actions runner responsive.
    """
    global _last_heartbeat_push
    now = time.monotonic()
    should_push = (not source_ok) or advanced or (now - _last_heartbeat_push >= 60)
    if should_push:
        _last_heartbeat_push = now
        return _original_heartbeat(
            source_ok=source_ok,
            source_url=source_url,
            source_latest=source_latest,
            stored_draw=stored_draw,
            advanced=advanced,
            error=error,
        )
    print({
        'idleCheck': True,
        'sourceLatest': source_latest,
        'storedDraw': stored_draw,
        'source': source_url,
    })
    return True


watcher.write_heartbeat = throttled_heartbeat

if __name__ == '__main__':
    watcher.main()
