#!/usr/bin/env python3
"""Build a validated Michigan Daily 3 historical archive.

Records are stored chronologically with separate midday/evening draws and all
three digits preserved. This archive is isolated from APX Cash Pop files.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path('daily3/archive.json')
SUMMARY = Path('daily3/archive_summary.json')
YEARS = range(2010, 2027)
SOURCES = (
    'https://michiganlotterynumbers.com/daily-3/numbers/{year}',
    'https://michigan.lottonumbers.com/daily-3/past-numbers/{year}',
)


def now():
    return datetime.now(timezone.utc).isoformat()


def fetch(url):
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; APX-Research/1.0)',
        'Cache-Control': 'no-cache',
    })
    with urlopen(req, timeout=90) as response:
        return response.read().decode('utf-8', 'ignore')


def visible_text(html):
    html = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.I)
    html = re.sub(r'<style[\s\S]*?</style>', ' ', html, flags=re.I)
    html = re.sub(r'<[^>]+>', '\n', html)
    replacements = {
        '&nbsp;': ' ', '&amp;': '&', '&#39;': "'", '&ndash;': '-', '&mdash;': '-',
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    return [re.sub(r'\s+', ' ', line).strip() for line in html.splitlines()
            if re.sub(r'\s+', ' ', line).strip()]


def parse_date(value):
    value = re.sub(r'\s+', ' ', value.replace(',', ' , ')).replace(' , ', ', ').strip()
    for fmt in ('%A, %B %d, %Y', '%B %d, %Y', '%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def normalize_number(token):
    digits = re.sub(r'\D', '', token)
    return digits if len(digits) == 3 else None


def parse_lines(lines, source):
    """Parse common archive layouts without assuming one exact HTML template."""
    rows = []
    date_rx = re.compile(
        r'^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+'
        r'[A-Za-z]+\s+\d{1,2},\s+\d{4}$', re.I)
    compact_date_rx = re.compile(r'^(?:[A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})$')
    draw_rx = re.compile(r'^(midday|evening|mid-day|night)\b', re.I)

    current_date = None
    for i, line in enumerate(lines):
        if date_rx.match(line) or compact_date_rx.match(line):
            current_date = parse_date(line)
            continue
        if not current_date:
            continue

        draw_match = draw_rx.match(line)
        if draw_match:
            draw_type = draw_match.group(1).lower()
            draw_type = 'midday' if draw_type in ('midday', 'mid-day') else 'evening'
            number = normalize_number(line)
            if not number:
                for j in range(i + 1, min(len(lines), i + 7)):
                    number = normalize_number(lines[j])
                    if number:
                        break
            if number:
                rows.append({
                    'date': current_date.isoformat(),
                    'drawType': draw_type,
                    'number': number,
                    'digits': [int(x) for x in number],
                    'source': source,
                })
                continue

        # Alternate layout: date followed by two labeled/unlabeled 3-digit results.
        if normalize_number(line):
            nearby = ' '.join(lines[max(0, i-2):i+1]).lower()
            if 'midday' in nearby or 'mid-day' in nearby:
                draw_type = 'midday'
            elif 'evening' in nearby or 'night' in nearby:
                draw_type = 'evening'
            else:
                continue
            number = normalize_number(line)
            rows.append({
                'date': current_date.isoformat(),
                'drawType': draw_type,
                'number': number,
                'digits': [int(x) for x in number],
                'source': source,
            })
    return rows


def main():
    collected = []
    source_report = []
    for year in YEARS:
        year_rows = []
        attempts = []
        for template in SOURCES:
            url = template.format(year=year)
            try:
                parsed = parse_lines(visible_text(fetch(url)), url)
                attempts.append({'url': url, 'rows': len(parsed), 'status': 'ok' if parsed else 'empty'})
                if len(parsed) > len(year_rows):
                    year_rows = parsed
            except Exception as exc:
                attempts.append({'url': url, 'rows': 0, 'status': 'error', 'error': repr(exc)})
        collected.extend(year_rows)
        source_report.append({'year': year, 'selectedRows': len(year_rows), 'attempts': attempts})

    # A date/draw type uniquely identifies a Daily 3 draw.
    unique = {}
    conflicts = []
    for row in collected:
        key = (row['date'], row['drawType'])
        if key in unique and unique[key]['number'] != row['number']:
            conflicts.append({'key': key, 'a': unique[key]['number'], 'b': row['number']})
        else:
            unique[key] = row

    order = {'midday': 0, 'evening': 1}
    draws = sorted(unique.values(), key=lambda r: (r['date'], order[r['drawType']]))
    for index, row in enumerate(draws, 1):
        row['sequence'] = index

    invalid_digits = sum(
        len(row['digits']) != 3 or any(d < 0 or d > 9 for d in row['digits'])
        for row in draws
    )
    duplicate_keys = len(collected) - len(unique)
    chronological = all(
        (draws[i-1]['date'], order[draws[i-1]['drawType']]) <=
        (draws[i]['date'], order[draws[i]['drawType']])
        for i in range(1, len(draws))
    )
    missing_partner_days = []
    by_date = {}
    for row in draws:
        by_date.setdefault(row['date'], set()).add(row['drawType'])
    for date, types in by_date.items():
        if types != {'midday', 'evening'}:
            missing_partner_days.append({'date': date, 'present': sorted(types)})

    canonical = '\n'.join(
        f"{r['sequence']},{r['date']},{r['drawType']},{r['number']}" for r in draws
    )
    sha = hashlib.sha256(canonical.encode()).hexdigest()
    archive = {
        'version': 1,
        'game': 'Michigan Daily 3',
        'updatedAt': now(),
        'drawCount': len(draws),
        'firstDate': draws[0]['date'] if draws else None,
        'latestDate': draws[-1]['date'] if draws else None,
        'sha256': sha,
        'validation': {
            'conflicts': len(conflicts),
            'duplicateSourceRowsCollapsed': duplicate_keys,
            'invalidDigitRows': invalid_digits,
            'chronological': chronological,
            'missingPartnerDayCount': len(missing_partner_days),
        },
        'sourceReport': source_report,
        'draws': draws,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(archive, indent=2))
    summary = {
        'version': archive['version'],
        'game': archive['game'],
        'drawCount': archive['drawCount'],
        'firstDate': archive['firstDate'],
        'latestDate': archive['latestDate'],
        'sha256': archive['sha256'],
        'validation': archive['validation'],
        'sampleFirst': draws[:3],
        'sampleLatest': draws[-3:],
    }
    SUMMARY.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
