#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import cloud_engine

SOURCE_URL = "https://cash-pop.com/michigan/winning-numbers"


def fetch_rendered_rows():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/127 Safari/537.36"
        )
        page.goto(SOURCE_URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(5000)
        html = page.content()
        browser.close()
    rows = cloud_engine.parse_html_draws(html)
    if not rows:
        raise RuntimeError("Rendered page loaded, but no draw records were parsed")
    return rows


if __name__ == "__main__":
    rows = fetch_rendered_rows()
    cloud_engine.fetch_draws = lambda: (rows, "cash-pop.com rendered browser")
    cloud_engine.main()
