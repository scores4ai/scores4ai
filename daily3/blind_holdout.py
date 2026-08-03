#!/usr/bin/env python3
import hashlib,json,random
from collections import Counter,defaultdict
from pathlib import Path

ARCHIVE=Path('daily3/archive.json'); OUT=Path('daily3/blind_holdout_results.json')

def exact_box(a,b): return a==b, sorted(a)==sorted(b)
def rand_pred(sha,seq):
 r=random.Random(int(hashlib.sha256(f'{sha}:blind:{seq}'.encode()).hexdigest()[:16],16));return [r.randrange(10) for _ in range(3)]
def freq_pred(rows): return [Counter(r['digits'][p] for r in rows).most_common(1)[0][0] for p in range(3)]
def trans_tables(rows):
 t=[[defaultdict(Counter) for _ in range(1)] for _ in range(3)]
 for a,b in zip(rows,rows[1:]):
  for p in range(3): t[p][0][a['digits'][p]][b['digits'][p]]+=1
 return t
def trans_pred(t,last,global_freq):
 out=[]
 for p in range(3):
  c=t[p][0][last[p]];out.append(c.most_common(1)[0][0] if c else global_freq[p])
 return out

def main():
 a=json.loads(ARCHIVE.read_text());d=a['draws'];n=len(d)
 train_end=int(n*.70); val_end=int(n*.85); hold=d[val_end:]
 locked=d[:val_end]; global_freq=freq_pred(locked); tables=trans_tables(locked)
 names=['uniform_random','frequency_position','last_draw','position_transition_1']
 s={x:{'tested':0,'exact':0,'box':0,'one':0,'pos':[0,0,0]} for x in names};samples=[]
 for i,row in enumerate(hold,val_end):
  actual=row['digits'];last=d[i-1]['digits']
  preds={'uniform_random':rand_pred(a['sha256'],row['sequence']),'frequency_position':global_freq,'last_draw':last,'position_transition_1':trans_pred(tables,last,global_freq)}
  fp=hashlib.sha256(json.dumps({'target':row['sequence'],'predictions':preds},sort_keys=True).encode()).hexdigest()
  for name,p in preds.items():
   hits=[p[j]==actual[j] for j in range(3)];ex,bx=exact_box(p,actual);z=s[name];z['tested']+=1;z['exact']+=ex;z['box']+=bx;z['one']+=any(hits)
   for j,h in enumerate(hits):z['pos'][j]+=h
  if len(samples)<30:samples.append({'sequence':row['sequence'],'predictionFingerprint':fp,'predictions':preds,'actual':actual})
 board=[]
 for name,z in s.items():
  q=z['tested'];board.append({'model':name,'tested':q,'exactHits':z['exact'],'exactAccuracy':z['exact']/q,'boxHits':z['box'],'boxAccuracy':z['box']/q,'atLeastOnePositionAccuracy':z['one']/q,'positionAccuracy':[x/q for x in z['pos']]})
 board.sort(key=lambda x:(-x['exactHits'],-sum(x['positionAccuracy']),x['model']))
 out={'version':'Daily 3 Blind Holdout Phase 1','archiveSha256':a['sha256'],'split':{'trainingDraws':train_end,'validationDraws':val_end-train_end,'blindHoldoutDraws':len(hold),'blindStartSequence':hold[0]['sequence'],'blindEndSequence':hold[-1]['sequence']},'integrity':{'holdoutLockedBeforeScoring':True,'holdoutUpdates':False,'futureDataAccess':False,'predictionsFrozenBeforeReveal':True},'randomBaselines':{'exactStraight':.001,'eachPosition':.1,'atLeastOnePosition':.271},'leaderboard':board,'samples':samples}
 raw=json.dumps(out,sort_keys=True,separators=(',',':'));out['resultSha256']=hashlib.sha256(raw.encode()).hexdigest();OUT.write_text(json.dumps(out,indent=2));print(json.dumps(board))
if __name__=='__main__':main()
