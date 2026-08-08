#!/usr/bin/env python3
import json,re,hashlib
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

YEARS=[2024,2025,2026]
URL='https://michiganlotterynumbers.com/cash-pop/numbers/{year}'
OUT=Path('research/cashpop_clean_archive.json')
META=Path('research/cashpop_clean_archive_meta.json')
UA={'User-Agent':'Mozilla/5.0 (compatible; scores4ai-research/1.0)'}

# Visible archive format is like: Wednesday, December 31, 2025 - 11:56PM then winning number.
DATE_RE=re.compile(r'((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}\s+-\s+\d{1,2}:\d{2}(?:AM|PM))',re.I)

def fetch_year(y):
    u=URL.format(year=y)
    r=requests.get(u,headers=UA,timeout=45)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser')
    text='\n'.join(s.strip() for s in soup.stripped_strings)
    matches=list(DATE_RE.finditer(text))
    rows=[]
    for i,m in enumerate(matches):
        start=m.end(); end=matches[i+1].start() if i+1<len(matches) else min(len(text),start+500)
        chunk=text[start:end]
        nm=re.search(r'(?<!\d)(1[0-5]|[1-9])(?!\d)',chunk)
        if not nm: continue
        raw=m.group(1)
        dt=datetime.strptime(re.sub(r'\s+',' ',raw.strip()),'%A, %B %d, %Y - %I:%M%p')
        rows.append({'timestamp':dt.strftime('%Y-%m-%dT%H:%M:00'),'number':int(nm.group(1)),'source':u})
    return rows,len(r.content)

def main():
    allrows=[]; sizes={}; per_year={}
    for y in YEARS:
        rows,size=fetch_year(y); sizes[str(y)]=size; per_year[str(y)]=len(rows); allrows.extend(rows)
    # Deduplicate exact timestamps. Conflicts are fatal.
    byts={}; conflicts=[]
    for r in allrows:
        ts=r['timestamp']
        if ts in byts and byts[ts]['number']!=r['number']: conflicts.append({'timestamp':ts,'a':byts[ts]['number'],'b':r['number']})
        else: byts[ts]=r
    if conflicts: raise SystemExit('timestamp conflicts: '+json.dumps(conflicts[:10]))
    clean=sorted(byts.values(),key=lambda r:r['timestamp'])
    if len(clean)<5000: raise SystemExit(f'archive too small: {len(clean)} rows; parser/source needs review')
    bad=[r for r in clean if not 1<=r['number']<=15]
    if bad: raise SystemExit('invalid numbers')
    # Frozen chronological split: 70/15/15. Final 15% is never to be used for model selection.
    n=len(clean); a=int(n*.70); b=int(n*.85)
    for i,r in enumerate(clean):
        r['partition']='discovery' if i<a else 'validation' if i<b else 'sealed_test'
    canonical='\n'.join(f"{r['timestamp']},{r['number']}" for r in clean)
    digest=hashlib.sha256(canonical.encode()).hexdigest()
    OUT.write_text(json.dumps({'schema':'timestamp,number,source,partition','draws':clean},indent=2))
    meta={'rows':n,'perYearParsed':per_year,'downloadBytes':sizes,'firstTimestamp':clean[0]['timestamp'],'lastTimestamp':clean[-1]['timestamp'],'discoveryRows':a,'validationRows':b-a,'sealedTestRows':n-b,'duplicateTimestampsRemoved':len(allrows)-len(clean),'conflicts':0,'sha256Canonical':digest,'sources':[URL.format(year=y) for y in YEARS]}
    META.write_text(json.dumps(meta,indent=2))
    print(json.dumps(meta,indent=2))
if __name__=='__main__': main()
