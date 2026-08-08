#!/usr/bin/env python3
import json,requests,re
from bs4 import BeautifulSoup
from pathlib import Path
u='https://cash-pop.com/michigan/past-winning-numbers'
r=requests.post(u,data={'date':'2026-07-29'},timeout=30,headers={'User-Agent':'Mozilla/5.0'})
r.raise_for_status(); s=BeautifulSoup(r.text,'html.parser')
strings=list(s.stripped_strings)
out={'status':r.status_code,'bytes':len(r.content),'strings':strings[:500],'drawMatches':re.findall(r'#(\d+)',r.text)[:300]}
Path('research/date_probe.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
