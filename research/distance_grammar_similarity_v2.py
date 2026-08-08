#!/usr/bin/env python3
import json, math, hashlib
from collections import Counter
from pathlib import Path
STATE=Path('v0/cloud_state.json'); OUT=Path('research/distance_grammar_similarity_v2_results.json')
WARMUP=260; MAX_LAG=15; BASELINE=.2
# LOCKED BEFORE RESULTS. Similar contexts are compared by categorical repeat geometry:
# 0=no recent repeat, 1=lag1-2, 2=lag3-5, 3=lag6-10, 4=lag11-15.
# Gate uses only prior analogous contexts; activate at >=6 weighted cases and
# Beta(1,4)-shrunk past hit rate >=25%, intended to yield materially more coverage.
MIN_CASES=6.; THRESH=.25

def pd(seq,i):
 v=seq[i]
 for d in range(1,MAX_LAG+1):
  if i-d<0: break
  if seq[i-d]==v:return d
 return 0

def ds(seq):return [pd(seq,i) for i in range(len(seq))]
def bucket(x):return 0 if x==0 else 1 if x<=2 else 2 if x<=5 else 3 if x<=10 else 4
def geom(d,end):return tuple(bucket(x) for x in d[end-3:end])
def sim(a,b):
 # 1 exact; 0.7 one bucket-step total; 0.4 two steps; else no analog
 dist=sum(abs(x-y) for x,y in zip(a,b))
 return 1.0 if dist==0 else .7 if dist==1 else .4 if dist==2 else 0.
def fallback(pre,used):
 c=Counter(pre[-120:]);return [n for n,_ in sorted(c.items(),key=lambda z:(z[1],-z[0]),reverse=True) if n not in used]
def predict(pre,d=None):
 d=d or ds(pre); cur=geom(d,len(d)); scores=Counter()
 for i in range(3,len(d)):
  g=geom(d,i); s=sim(g,cur)
  if not s:continue
  nxt=d[i]
  if 1<=nxt<=MAX_LAG:scores[pre[-nxt]]+=s*(1+1/(1+nxt))
 picks=[n for n,_ in scores.most_common()]
 for n in fallback(pre,set(picks)):
  picks.append(n)
  if len(picks)>=3:break
 return picks[:3]
def gate(pre):
 d=ds(pre); cur=geom(d,len(d)); cases=hits=0.
 for t in range(45,len(pre)):
  s=sim(geom(d,t),cur)
  if not s:continue
  hist=pre[:t]; p=predict(hist);cases+=s;hits+=s*int(pre[t] in p)
 rate=(hits+1)/(cases+5)
 return cases>=MIN_CASES and rate>=THRESH,cases,hits,rate,cur
def tail(k,n,p):return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k,n+1))
def main():
 st=json.loads(STATE.read_text()); draws=sorted(st['draws'],key=lambda x:int(x['draw'])); nums=[int(x['number']) for x in draws]
 rec=[];fails=[];chain='GENESIS'
 for t in range(WARMUP,len(nums)):
  pre=nums[:t]; g=gate(pre); p=predict(pre)
  # suffix mutation invariant
  mut=nums[:t]+[((x+7-1)%15)+1 for x in nums[t:]]; mg=gate(mut[:t]);mp=predict(mut[:t])
  if (g[0],round(g[1],9),round(g[2],9),round(g[3],12),g[4],p)!=(mg[0],round(mg[1],9),round(mg[2],9),round(mg[3],12),mg[4],mp):fails.append(int(draws[t]['draw']))
  if g[0]:
   hit=nums[t] in p;rec.append({'draw':int(draws[t]['draw']),'trainingThrough':int(draws[t-1]['draw']),'geometry':g[4],'weightedPastCases':g[1],'weightedPastHits':g[2],'smoothedPastRate':g[3],'picks':p,'actual':nums[t],'hit':hit});chain=hashlib.sha256(f'{chain}|{draws[t]["draw"]}|{g[4]}|{p}'.encode()).hexdigest()[:20]
 n=len(rec);h=sum(r['hit'] for r in rec);elig=max(0,len(nums)-WARMUP);acc=h/n if n else 0
 out={'experiment':'Similarity-Gated Repeat-Distance Grammar v2 LOCKED','locked':{'warmup':WARMUP,'picks':3,'baseline':BASELINE,'buckets':'0,1-2,3-5,6-10,11-15','similarityWeights':{'distance0':1,'distance1':.7,'distance2':.4},'minWeightedCases':MIN_CASES,'activationSmoothedRate':THRESH},'integrity':{'futureMutationFailures':fails,'passed':not fails,'hashTail':chain},'eligibleTargets':elig,'activations':n,'coverage':n/max(1,elig),'hits':h,'accuracy':acc,'excessPercentagePoints':(acc-BASELINE)*100,'oneSidedBinomialPValue':tail(h,n,BASELINE) if n else None,'records':rec}
 OUT.write_text(json.dumps(out,indent=2));print(json.dumps({k:out[k] for k in ['activations','coverage','hits','accuracy','excessPercentagePoints','oneSidedBinomialPValue']},indent=2))
if __name__=='__main__':main()
