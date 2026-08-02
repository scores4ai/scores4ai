#!/usr/bin/env python3
import html
import re
import time
from urllib.request import Request, urlopen

import github_updater as engine

BASE = "https://cash-pop.com/michigan/winning-numbers"
ORIGINAL_BROWSER_FETCH = engine.fetch_visible_text


def html_to_visible_text(document: str) -> str:
    """Convert fetched HTML into the line-oriented text expected by engine.parse."""
    document = re.sub(r"(?is)<script[^>]*>.*?</script>", "\n", document)
    document = re.sub(r"(?is)<style[^>]*>.*?</style>", "\n", document)
    document = re.sub(r"(?i)<br\s*/?>", "\n", document)
    document = re.sub(r"(?i)</(?:div|p|li|section|article|h[1-6]|tr|td|span|a)>", "\n", document)
    document = re.sub(r"(?s)<[^>]+>", " ", document)
    document = html.unescape(document).replace("\xa0", " ")
    return "\n".join(line.strip() for line in document.splitlines() if line.strip())


def fetch_direct(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18 Mobile Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
    with urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8", "ignore")


def direct_fetch() -> str:
    candidates = []
    stamp = str(time.time_ns())

    for suffix in (
        "?nocache=" + stamp,
        "/?nocache=" + stamp,
        "?v=" + stamp + "&source=github",
    ):
        url = BASE + suffix
        try:
            raw_html = fetch_direct(url)
            visible = html_to_visible_text(raw_html)
            rows = engine.parse(visible)
            if rows:
                latest = max(row["draw"] for row in rows)
                candidates.append((latest, visible, "direct"))
                print("Direct candidate:", latest, url)
            else:
                print("Direct source parsed zero rows:", url)
        except Exception as exc:
            print("Direct fetch failed:", url, repr(exc))

    try:
        visible = ORIGINAL_BROWSER_FETCH()
        rows = engine.parse(visible)
        if rows:
            latest = max(row["draw"] for row in rows)
            candidates.append((latest, visible, "browser"))
            print("Browser candidate:", latest)
        else:
            print("Browser source parsed zero rows")
    except Exception as exc:
        print("Browser fetch failed:", repr(exc))

    if not candidates:
        raise RuntimeError("All live-result fetch methods failed or returned unparseable data")

    candidates.sort(key=lambda item: item[0], reverse=True)
    latest, text, source = candidates[0]
    print("Selected source:", source, "latest draw:", latest)
    return text


engine.fetch_visible_text = direct_fetch
engine.main()
