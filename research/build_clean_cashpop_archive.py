#!/usr/bin/env python3
import json,re,time,hashlib,requests
from bs4 import BeautifulSoup
from datetime import date,timedelta,datetime
from pathlib import Path
URL='https://cash-pop.com/michigan/past-winning-numbers'
START=date(2026,6,20); END=date(2026,8,7)
OUT=Path('research/clean_cashpop_archive.json'); META=Path('research/archive_metadata.json')
HEAD={'User-Agent':'Mozilla/5.0 (compatible; APX research archive verifier/1.0)'}
TIME_RE=re.compile(r'^\d{1,2}:\d{2}\s(?:AM|PM)$'); DRAW_RE=re.compile(r'^#(\d+)$'); NUM_RE=re.compile(r'^(?:[1-9]|1[0-5])$')
def parse_day(day):
 r=requests.post(URL,data={'date':day.isoformat()},headers=HEAD,timeout=45); r.raise_for_status(); toks=list(BeautifulSoup(r.text,'html.parser').stripped_strings); rows=[]
 for i,t in enumerate(toks):
  m=DRAW_RE.match(t)
  if m and i>0 and i+1<len(toks) and NUM_RE.match(toks[i-1].strip()) and TIME_RE.match(toks[i+1].strip()): rows.append({'draw':int(m.group(1)),'number':int(toks[i-1]),'date':day.isoformat(),'time':toks[i+1].strip(),'source':URL})
 return rows,len(r.content)
def main():
 by={}; conflicts=[]; per=[]; totalbytes=0; d=START
 while d<=END:
  rows,b=parse_day(d); totalbytes+=b; per.append({'date':d.isoformat(),'rows':len(rows)})
  for row in rows:
   old=by.get(row['draw'])
   if old and (old['number'],old['date'],old['time'])!=(row['number'],row['date'],row['time']): conflicts.append({'draw':row['draw'],'first':old,'second':row})
   else: by[row['draw']]=row
  print(d,len(rows),'unique',len(by)); time.sleep(.10); d+=timedelta(days=1)
 rows=sorted(by.values(),key=lambda x:x['draw'])
 if conflicts: raise SystemExit('conflicting duplicates: '+str(len(conflicts)))
 if any(not 1<=r['number']<=15 for r in rows): raise SystemExit('invalid winning number')
 if len(rows)<5000: raise SystemExit(f'archive too small: {len(rows)}')
 ids=[r['draw'] for r in rows]; have=set(ids); missing=[n for n in range(ids[0],ids[-1]+1) if n not in have]
 canonical=json.dumps(rows,separators=(',',':'),sort_keys=True); digest=hashlib.sha256(canonical.encode()).hexdigest(); n=len(rows); a=int(n*.70); b=int(n*.85)
 OUT.write_text(json.dumps({'draws':rows},indent=2))
 meta={'status':'READY','source':URL,'sourceMethod':'POST date','startDate':START.isoformat(),'endDate':END.isoformat(),'rows':n,'firstDraw':rows[0]['draw'],'lastDraw':rows[-1]['draw'],'missingDrawIds':missing,'missingCount':len(missing),'conflicts':0,'invalidNumbers':0,'days':len(per),'downloadBytes':totalbytes,'perDay':per,'sha256':digest,'partition':{'discovery':[0,a],'validation':[a,b],'sealedTest':[b,n]},'sealedTestRows':n-b,'generatedUtc':datetime.utcnow().isoformat(timespec='seconds')+'Z'}
 META.write_text(json.dumps(meta,indent=2)); print(json.dumps({k:meta[k] for k in ['status','rows','firstDraw','lastDraw','missingCount','sealedTestRows','sha256']},indent=2))
if __name__=='__main__': main()
