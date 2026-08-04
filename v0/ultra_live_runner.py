#!/usr/bin/env python3
"""Run the validated Cash Pop watcher continuously at low latency."""
import time
import minute_watcher as watcher

# Poll every five seconds for about 55 minutes. The workflow starts another
# warm runner every 30 minutes so source monitoring remains continuous.
watcher.INTERVAL = 5
watcher.CHECKS = 660

_original_heartbeat = watcher.write_heartbeat
_last_heartbeat_push = 0.0


def throttled_heartbeat(*, source_ok, source_url, source_latest, stored_draw,
                         advanced, error=None):
    """Commit idle health at most once per minute; publish failures immediately."""
    global _last_heartbeat_push
    current = time.monotonic()
    should_push = (not source_ok) or advanced or (current - _last_heartbeat_push >= 60)
    if should_push:
        _last_heartbeat_push = current
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
