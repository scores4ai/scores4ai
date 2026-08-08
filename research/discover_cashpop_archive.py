#!/usr/bin/env python3
import json, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
URL='https://cash-pop.com/michigan/past-winning-numbers'
OUT=Path('research/archive_discovery.json')
r=requests.get(URL,timeout=30,headers={'User-Agent':'Mozilla/5.0'})
r.raise_for_status()
s=BeautifulSoup(r.text,'html.parser')
forms=[]
for f in s.find_all('form'):
    forms.append({
      'action':urljoin(URL,f.get('action') or ''),
      'method':(f.get('method') or 'get').lower(),
      'inputs':[{'name':i.get('name'),'type':i.get('type'),'value':i.get('value'),'placeholder':i.get('placeholder')} for i in f.find_all('input')],
      'selects':[{'name':sel.get('name'),'options':[o.get('value') for o in sel.find_all('option')]} for sel in f.find_all('select')]
    })
links=[]
for a in s.find_all('a',href=True):
    href=urljoin(URL,a['href'])
    if 'michigan' in href and ('winning' in href or 'draw' in href):
        links.append(href)
links=sorted(set(links))
text=' '.join(s.stripped_strings)
out={'url':URL,'status':r.status_code,'bytes':len(r.content),'forms':forms,'links':links[:200],'sampleText':text[:4000]}
OUT.write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
