#!/usr/bin/env python3
import json, math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SOURCE=Path('v0/cloud_state.json');OUT=Path('apx/state.json');NUMBERS=range(1,16);BASELINE=5/15

def norm(s):
 t=sum(s.values()) or 1;return {n:s.get(n,0)/t for n in NUMBERS}
def frequency(seq,window=None,decay=None):
 s={n:.25 for n in NUMBERS};data=seq[-window:] if window else seq
 if decay:
  for age,x in enumerate(reversed(data)):s[x]+=decay**age
 else:
  for x in data:s[x]+=1
 return norm(s)
def gap_model(seq,overdue=True):
 s={n:.1 for n in NUMBERS};rev=list(reversed(seq))
 for n in NUMBERS:
  try:g=rev.index(n)+1
  except ValueError:g=len(seq)+1
  s[n]=g if overdue else 1/max(g,1)
 return norm(s)
def markov(seq,order=1):
 s={n:.25 for n in NUMBERS}
 if len(seq)<=order:return norm(s)
 key=tuple(seq[-order:])
 for i in range(order,len(seq)):
  if tuple(seq[i-order:i])==key:s[seq[i]]+=1
 return norm(s)
def lag(seq,k):
 s={n:.25 for n in NUMBERS}
 if len(seq)>=k:s[seq[-k]]+=5
 return norm(s)
def cycle(seq,k):
 s={n:.25 for n in NUMBERS};slot=len(seq)%k
 for i,x in enumerate(seq):
  if i%k==slot:s[x]+=1
 return norm(s)
def neighbor(seq,length=4):
 s={n:.25 for n in NUMBERS}
 if len(seq)<=length:return norm(s)
 tail=seq[-length:]
 for i in range(length,len(seq)):
  d=sum(a!=b for a,b in zip(tail,seq[i-length:i]));s[seq[i]]+=1/(1+d)
 return norm(s)
def build_models(seq):
 m={}
 for w in (10,20,30,50,75,100,200,None):m[f'freq_{w or "all"}']=frequency(seq,w)
 for d in (.90,.94,.97,.985):m[f'decay_{d}']=frequency(seq,decay=d)
 for o in (1,2,3):m[f'markov_{o}']=markov(seq,o)
 for k in (2,3,5,7,8,13,21):m[f'lag_{k}']=lag(seq,k)
 for k in (3,4,5,6,7,8,9,10,12,15,20,30):m[f'cycle_{k}']=cycle(seq,k)
 m['gap_overdue']=gap_model(seq,True);m['gap_recent']=gap_model(seq,False)
 for l in (3,4,5,6):m[f'neighbor_{l}']=neighbor(seq,l)
 return m
def picks(s):return [n for n,_ in sorted(s.items(),key=lambda x:(-x[1],x[0]))[:5]]
def fresh_record():return {'tested':0,'hits':0,'recent':[],'weight':1.0}
def train(draws,warmup=100):
 records=defaultdict(fresh_record);history=[];seq=[]
 for row in draws:
  if len(seq)>=warmup:
   models=build_models(seq);votes={n:0.0 for n in NUMBERS};model_picks={}
   for name,s in models.items():
    p=picks(s);model_picks[name]=p;r=records[name];recent=sum(r['recent'][-50:])/max(1,len(r['recent'][-50:]));r['weight']=max(.05,min(8.0,math.exp(3*(recent-BASELINE))))
    for n,v in s.items():votes[n]+=v*r['weight']
   ensemble=picks(votes);actual=row['number'];hit=actual in ensemble;history.append({'draw':row['draw'],'top5':ensemble,'actual':actual,'hit5':hit,'type':'strict_walk_forward'})
   for name,p in model_picks.items():
    h=1 if actual in p else 0;r=records[name];r['tested']+=1;r['hits']+=h;r['recent'].append(h);r['recent']=r['recent'][-200:]
  seq.append(row['number'])
 models=build_models(seq);votes={n:0.0 for n in NUMBERS};model_picks={}
 for name,s in models.items():
  p=picks(s);model_picks[name]=p;r=records[name];recent=sum(r['recent'][-50:])/max(1,len(r['recent'][-50:]));r['weight']=max(.05,min(8.0,math.exp(3*(recent-BASELINE))))
  for n,v in s.items():votes[n]+=v*r['weight']
 board=[]
 for name,r in records.items():
  acc=r['hits']/r['tested'] if r['tested'] else 0;r50=sum(r['recent'][-50:])/max(1,len(r['recent'][-50:]));board.append({'name':name,'tested':r['tested'],'hits':r['hits'],'accuracy':acc,'rolling50':r50,'weight':r['weight'],'top5':model_picks.get(name,[])})
 board.sort(key=lambda x:(-x['weight'],-x['rolling50'],-x['accuracy']))
 return history,board,picks(votes),model_picks

def wilson(h,n,z=1.959963984540054):
 if n<=0:return [0,1]
 p=h/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;m=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/d;return [max(0,c-m),min(1,c+m)]
def binomial_tail(h,n,p=BASELINE):
 if n<=0:return 1.0
 logs=[math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)+k*math.log(p)+(n-k)*math.log1p(-p) for k in range(h,n+1)]
 mx=max(logs);return min(1.0,math.exp(mx)*sum(math.exp(x-mx) for x in logs))
def integrity(history):
 n=len(history);h=sum(1 for x in history if x.get('hit5'));obs=h/n if n else 0;lo,hi=wilson(h,n);pv=binomial_tail(h,n);recent=history[-100:];previous=history[-200:-100];ra=sum(x.get('hit5',False) for x in recent)/len(recent) if recent else 0;pa=sum(x.get('hit5',False) for x in previous)/len(previous) if previous else None;delta=ra-pa if pa is not None else 0
 trend='flat' if pa is None or abs(delta)<.015 else ('improving' if delta>0 else 'declining');sig=pv<.05 and lo>BASELINE;evidence='strong' if sig and pv<.001 else ('moderate' if sig else 'insufficient')
 return {'baseline':BASELINE,'observed':obs,'excess':obs-BASELINE,'confidence95':{'low':lo,'high':hi},'pValueOneSided':pv,'independentPredictions':n,'significantAt05':sig,'evidence':evidence,'trend':trend,'recent100':ra,'previous100':pa,'trendDelta':delta,'note':'Exploratory walk-forward evidence; multiple-model selection is not yet corrected.'}
def main():
 src=json.loads(SOURCE.read_text());draws=src.get('draws',[])
 if len(draws)<120:raise SystemExit('Need at least 120 draws')
 history,board,top5,model_picks=train(draws);latest=max(x['draw'] for x in draws);hits=sum(x['hit5'] for x in history);live=[x for x in src.get('history',[]) if x.get('type')=='automated_future_test'];ri=integrity(history)
 feed=src.get('feedDiagnostics') or {};feed['sourceLabel']=src.get('feed','unknown');feed['sourceUrl']=src.get('source','');feed['sourceUpdatedAt']=src.get('updatedAt');feed['apxLatestDraw']=latest;feed['sourceLatestDraw']=src.get('latestDraw',latest);feed['drawGap']=max(0,int(feed['sourceLatestDraw'])-int(latest))
 out={'version':'APX Phase 1.2','updatedAt':datetime.now(timezone.utc).isoformat(),'latestDraw':latest,'nextDraw':latest+1,'top5':top5,'drawCount':len(draws),'modelCount':len(board),'leaderboard':board,'history':history[-300:],'liveHistory':live[-300:],'researchIntegrity':ri,'feedDiagnostics':feed,'stats':{'evaluated':len(history),'hits':hits,'misses':len(history)-hits,'accuracy':hits/len(history) if history else 0,'randomTop5Baseline':BASELINE,'liveEvaluated':len(live),'liveHits':sum(1 for x in live if x.get('hit5'))},'modelTop5':model_picks}
 OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(out,indent=2));print(json.dumps({'latest':latest,'next':latest+1,'models':len(board),'top5':top5,'feed':feed.get('selectedSource',feed.get('sourceLabel')),'gap':feed['drawGap']}))
if __name__=='__main__':main()
