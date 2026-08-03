#!/usr/bin/env python3
import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

OUT=Path('apx/full_archive.json'); LIVE=Path('v0/cloud_state.json')
YEARS=(2024,2025,2026)
URL='https://michiganlotterynumbers.com/cash-pop/numbers/{year}'


def now(): return datetime.now(timezone.utc).isoformat()

def fetch(url):
 req=Request(url,headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'})
 with urlopen(req,timeout=90) as r:return r.read().decode('utf-8','ignore')

def text(html):
 html=re.sub(r'<script[\s\S]*?</script>',' ',html,flags=re.I)
 html=re.sub(r'<style[\s\S]*?</style>',' ',html,flags=re.I)
 html=re.sub(r'<[^>]+>','\n',html)
 html=html.replace('&nbsp;',' ').replace('&#39;',"'").replace('&amp;','&')
 return [re.sub(r'\s+',' ',x).strip() for x in html.splitlines() if re.sub(r'\s+',' ',x).strip()]

def parse_dt(s):
 s=re.sub(r'\s+',' ',s.replace('–','-').replace('—','-')).strip()
 for fmt in ('%A, %B %d, %Y - %I:%M%p','%A, %B %d, %Y - %I:%M %p','%A %B %d %Y %I:%M %p'):
  try:return datetime.strptime(s,fmt)
  except ValueError:pass
 return None

def parse(lines,year,source):
 rx=re.compile(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Za-z]+\s+\d{1,2},\s*\d{4})\s*-\s*(\d{1,2}:\d{2}\s*(?:AM|PM))$',re.I)
 out=[]
 for i,line in enumerate(lines):
  m=rx.match(line)
  if not m or not m.group(2).endswith(str(year)):continue
  dt=parse_dt(f'{m.group(1)}, {m.group(2)} - {m.group(3)}')
  if not dt:continue
  number=None
  for j in range(i+1,min(len(lines),i+8)):
   if lines[j].isdigit() and 1<=int(lines[j])<=15:number=int(lines[j]);break
  if number:out.append({'dt':dt,'number':number,'date':m.group(2),'time':m.group(3).upper(),'source':source})
 return out

def live_rows():
 d=json.loads(LIVE.read_text())
 out=[]
 for r in d.get('draws',[]):
  raw=f"{r.get('date','')} - {r.get('time','')}"
  dt=parse_dt(raw)
  if dt:out.append((dt,int(r['number']),int(r['draw']),r))
 return out

def main():
 rows=[];report=[]
 for y in YEARS:
  u=URL.format(year=y)
  try:
   r=parse(text(fetch(u)),y,u);rows+=r;report.append({'year':y,'source':u,'rows':len(r),'status':'ok' if r else 'empty'})
  except Exception as e:report.append({'year':y,'source':u,'rows':0,'status':'error','error':repr(e)})
 # unique timestamp; conflicting duplicates abort
 by={}
 for r in rows:
  k=r['dt']
  if k in by and by[k]['number']!=r['number']:raise SystemExit(f'conflicting result at {k}')
  by[k]=r
 rows=[by[k] for k in sorted(by)]
 live=live_rows();live_map={(dt,n):draw for dt,n,draw,_ in live}
 anchors=[(i,live_map[(r['dt'],r['number'])]) for i,r in enumerate(rows) if (r['dt'],r['number']) in live_map]
 if not anchors:raise SystemExit('No timestamp+number anchor found against live data')
 # Verify all anchors imply the same offset; tolerate isolated bad source rows only by aborting.
 offsets=[draw-i for i,draw in anchors]
 offset=max(set(offsets),key=offsets.count)
 agreeing=sum(x==offset for x in offsets)
 if agreeing<max(1,int(len(offsets)*0.95)):raise SystemExit(f'Anchor disagreement: {agreeing}/{len(offsets)}')
 canonical=[]
 for i,r in enumerate(rows):
  canonical.append({'draw':offset+i,'number':r['number'],'date':r['date'],'time':r['time'],'source':r['source']+' timestamp anchored'})
 # Merge exact live records, rejecting conflicts.
 merged={int(r['draw']):r for r in canonical}
 for _,_,draw,r in live:
  if draw in merged and int(merged[draw]['number'])!=int(r['number']):raise SystemExit(f'live conflict draw {draw}')
  merged[draw]={**r,'draw':draw,'number':int(r['number']),'source':r.get('source') or 'live APX'}
 draws=[merged[k] for k in sorted(merged)]
 payload='\n'.join(f"{r['draw']},{r['number']},{r.get('date','')},{r.get('time','')}" for r in draws)
 ids=[r['draw'] for r in draws]
 out={'version':2,'immutableAppendOnly':True,'updatedAt':now(),'drawCount':len(draws),'firstDraw':ids[0],'latestDraw':ids[-1],'sha256':hashlib.sha256(payload.encode()).hexdigest(),'anchor':{'matches':len(anchors),'agreeing':agreeing,'offset':offset},'validation':{'duplicateDrawIds':len(ids)-len(set(ids)),'numbersOutside1To15':sum(not 1<=r['number']<=15 for r in draws),'chronological':ids==sorted(ids),'missingDrawIdCount':sum(max(0,b-a-1) for a,b in zip(ids,ids[1:]))},'sources':report,'draws':draws}
 OUT.write_text(json.dumps(out,indent=2));print(json.dumps({k:out[k] for k in ('drawCount','firstDraw','latestDraw','sha256')}))
if __name__=='__main__':main()
