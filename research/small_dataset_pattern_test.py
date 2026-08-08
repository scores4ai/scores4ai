#!/usr/bin/env python3
import json, math
from collections import Counter
from pathlib import Path
SRC=Path('v0/cloud_state.json'); OUT=Path('research/small_dataset_pattern_results.json')
# LOCKED: use only actual draw rows; chronological; first 400 discovery/warmup, last 200 sealed walk-forward.
# Three candidates per target. Compare literal repeat-gap grammar, recent lag vote, and consensus.

def gap(seq,i,maxlag=15):
 v=seq[i]
 for d in range(1,min(maxlag,i)+1):
  if seq[i-d]==v:return d
 return 0

def grammar(pre):
 ds=[gap(pre,i) for i in range(len(pre))]; ctx=tuple(ds[-3:]); sc=Counter()
 for i in range(3,len(ds)):
  hist=tuple(ds[i-3:i]); similarity=sum((3-j) for j in range(3) if hist[j]==ctx[j])
  if similarity and 1<=ds[i]<=15: sc[pre[-ds[i]]]+=similarity
 return [n for n,_ in sc.most_common(3)]

def lagvote(pre):
 sc=Counter()
 for lag in range(1,16):
  matches=tries=0
  for i in range(max(lag,1),len(pre)):
   tries+=1;matches+=pre[i]==pre[i-lag]
  lift=(matches+1)/(tries+15) if tries else 0
  sc[pre[-lag]]+=lift*(1+1/lag)
 return [n for n,_ in sc.most_common(3)]

def fill(p,pre):
 p=list(dict.fromkeys(p)); c=Counter(pre[-100:])
 for n,_ in c.most_common():
  if n not in p:p.append(n)
  if len(p)==3:break
 return p[:3]
def tail(k,n,p=.2):return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k,n+1))
def main():
 st=json.loads(SRC.read_text()); raw=st['draws']; rows=[];seen=set()
 for r in raw:
  try:d=int(r['draw']);n=int(r['number'])
  except:continue
  if 1<=n<=15 and d not in seen:rows.append((d,n));seen.add(d)
 rows.sort(); rows=rows[-600:]
 nums=[n for _,n in rows]; start=max(100,len(nums)-200); rec=[]
 for t in range(start,len(nums)):
  pre=nums[:t]; a=fill(grammar(pre),pre); b=fill(lagvote(pre),pre)
  votes=Counter(a+b); c=[n for n,_ in sorted(votes.items(),key=lambda kv:(kv[1],-kv[0]),reverse=True)[:3]]; c=fill(c,pre)
  actual=nums[t]; rec.append({'draw':rows[t][0],'grammar':a,'lagVote':b,'consensus':c,'actual':actual,'gHit':actual in a,'lHit':actual in b,'cHit':actual in c})
 out={'experiment':'Small dataset sealed pattern test','datasetRows':len(rows),'testRows':len(rec),'firstDraw':rows[0][0],'lastDraw':rows[-1][0],'baseline':.2,'models':{},'records':rec}
 for key,label in [('gHit','Repeat-Distance Grammar'),('lHit','Lag Vote'),('cHit','Consensus')]:
  h=sum(r[key] for r in rec);n=len(rec);acc=h/n
  out['models'][label]={'hits':h,'tests':n,'accuracy':acc,'excessPP':(acc-.2)*100,'oneSidedP':tail(h,n)}
 OUT.write_text(json.dumps(out,indent=2));print(json.dumps(out['models'],indent=2))
if __name__=='__main__':main()
