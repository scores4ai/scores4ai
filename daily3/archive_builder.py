#!/usr/bin/env python3
"""Build a validated Michigan Daily 3 archive from year pages.

Each archive date is followed by three midday digits and three evening digits.
The result is stored oldest-to-newest and isolated from Cash Pop research.
"""
import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

OUT=Path('daily3/archive.json')
SUMMARY=Path('daily3/archive_summary.json')
YEARS=range(2010,2027)
URL='https://michigan.lottonumbers.com/daily-3/past-numbers/{year}'


def now(): return datetime.now(timezone.utc).isoformat()

def fetch(url):
 req=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; APX-Research/1.0)','Cache-Control':'no-cache'})
 with urlopen(req,timeout=90) as r:return r.read().decode('utf-8','ignore')

def lines(html):
 html=re.sub(r'<script[\s\S]*?</script>',' ',html,flags=re.I)
 html=re.sub(r'<style[\s\S]*?</style>',' ',html,flags=re.I)
 html=re.sub(r'<[^>]+>','\n',html)
 html=html.replace('&nbsp;',' ').replace('&amp;','&')
 return [re.sub(r'\s+',' ',x).strip() for x in html.splitlines() if re.sub(r'\s+',' ',x).strip()]

def parse_year(text,source):
 date_rx=re.compile(r'^(\d{1,2}/\d{1,2}/\d{4})$')
 rows=[]
 for i,line in enumerate(text):
  m=date_rx.match(line)
  if not m:continue
  try: day=datetime.strptime(m.group(1),'%m/%d/%Y').date().isoformat()
  except ValueError:continue
  digits=[]
  for j in range(i+1,min(len(text),i+18)):
   token=text[j].strip()
   if date_rx.match(token):break
   if re.fullmatch(r'[0-9]',token):digits.append(int(token))
   if len(digits)==6:break
  if len(digits)==6:
   for draw_type,part in [('midday',digits[:3]),('evening',digits[3:])]:
    rows.append({'date':day,'drawType':draw_type,'number':''.join(map(str,part)),'digits':part,'source':source})
 return rows

def main():
 collected=[];report=[]
 for year in YEARS:
  url=URL.format(year=year)
  try:
   parsed=parse_year(lines(fetch(url)),url)
   report.append({'year':year,'rows':len(parsed),'status':'ok' if parsed else 'empty','source':url})
   collected.extend(parsed)
  except Exception as exc:
   report.append({'year':year,'rows':0,'status':'error','source':url,'error':repr(exc)})
 unique={};conflicts=[]
 for row in collected:
  key=(row['date'],row['drawType'])
  if key in unique and unique[key]['number']!=row['number']:
   conflicts.append({'date':row['date'],'drawType':row['drawType'],'a':unique[key]['number'],'b':row['number']})
  else:unique[key]=row
 order={'midday':0,'evening':1}
 draws=sorted(unique.values(),key=lambda r:(r['date'],order[r['drawType']]))
 for i,row in enumerate(draws,1):row['sequence']=i
 invalid=sum(len(r['digits'])!=3 or any(d<0 or d>9 for d in r['digits']) for r in draws)
 chronological=all((draws[i-1]['date'],order[draws[i-1]['drawType']]) <= (draws[i]['date'],order[draws[i]['drawType']]) for i in range(1,len(draws)))
 by_date={}
 for row in draws:by_date.setdefault(row['date'],set()).add(row['drawType'])
 missing=[d for d,t in by_date.items() if t!={'midday','evening'}]
 canonical='\n'.join(f"{r['sequence']},{r['date']},{r['drawType']},{r['number']}" for r in draws)
 archive={'version':2,'game':'Michigan Daily 3','updatedAt':now(),'drawCount':len(draws),'firstDate':draws[0]['date'] if draws else None,'latestDate':draws[-1]['date'] if draws else None,'sha256':hashlib.sha256(canonical.encode()).hexdigest(),'validation':{'conflicts':len(conflicts),'duplicateRowsCollapsed':len(collected)-len(unique),'invalidDigitRows':invalid,'chronological':chronological,'missingPartnerDayCount':len(missing)},'sourceReport':report,'draws':draws}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(archive,indent=2))
 summary={k:archive[k] for k in ('version','game','drawCount','firstDate','latestDate','sha256','validation')};summary['sampleFirst']=draws[:2];summary['sampleLatest']=draws[-2:]
 SUMMARY.write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
