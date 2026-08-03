#!/usr/bin/env python3
"""Train a non-voting contextual model selector and judge it on untouched draws.

The selector learns only from the training block. During the holdout block its
policy is locked: it receives pre-draw features and base-model predictions, but
never updates from holdout outcomes.
"""
import hashlib, json, math
from collections import Counter, defaultdict
from pathlib import Path

ARCHIVE=Path('apx/full_archive.json')
OUT=Path('apx/meta_model_results.json')
NUMBERS=tuple(range(1,16))
WARMUP=200
TRAIN=5000
HOLDOUT=3000
BASELINE=5/15


def top5(scores):
 return [n for n,_ in sorted(scores.items(),key=lambda x:(-x[1],x[0]))[:5]]

def frequency(seq,window=None):
 s=seq[-window:] if window else seq;c=Counter(s)
 return top5({n:c[n]+.5 for n in NUMBERS})

def gap(seq):
 rev=list(reversed(seq));d={}
 for n in NUMBERS:
  try:d[n]=rev.index(n)+1
  except ValueError:d[n]=len(seq)+1
 return top5(d)

def markov(seq):
 if not seq:return list(NUMBERS[:5])
 last=seq[-1];c=Counter(b for a,b in zip(seq,seq[1:]) if a==last)
 return top5({n:c[n]+.25 for n in NUMBERS}) if c else frequency(seq,60)

def cycle(seq,p):
 slot=len(seq)%p;c=Counter(x for i,x in enumerate(seq) if i%p==slot)
 return top5({n:c[n]+.25 for n in NUMBERS})

def lag_vote(seq):
 s={n:0.0 for n in NUMBERS}
 for lag,w in ((2,3),(3,2.5),(5,2),(8,1.5),(13,1)):
  if len(seq)>=lag:s[seq[-lag]]+=w
 return top5(s)

MODELS={
 'cycle_8':lambda s:cycle(s,8),'markov_1':markov,'frequency_all':lambda s:frequency(s),
 'gap_longest':gap,'lag_vote':lag_vote,'frequency_24':lambda s:frequency(s,24),
 'cycle_20':lambda s:cycle(s,20),'frequency_60':lambda s:frequency(s,60),
}

def entropy_bucket(seq):
 s=seq[-50:];c=Counter(s);h=-sum((v/len(s))*math.log(v/len(s),15) for v in c.values()) if s else 0
 return 'low' if h<.88 else ('mid' if h<.95 else 'high')

def repeat_bucket(seq):
 s=seq[-30:];r=sum(a==b for a,b in zip(s,s[1:]))/max(1,len(s)-1)
 return 'low' if r<.04 else ('mid' if r<.09 else 'high')

def band_bucket(seq):
 s=seq[-30:];low=sum(x<=7 for x in s)/max(1,len(s))
 return 'low-heavy' if low>.60 else ('high-heavy' if low<.40 else 'balanced')

def parity_bucket(seq):
 s=seq[-30:];odd=sum(x%2 for x in s)/max(1,len(s))
 return 'odd-heavy' if odd>.60 else ('even-heavy' if odd<.40 else 'balanced')

def context(seq):
 return (entropy_bucket(seq),repeat_bucket(seq),band_bucket(seq),parity_bucket(seq))

def wilson(h,n,z=1.959963984540054):
 if not n:return [0,1]
 p=h/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;m=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/d
 return [max(0,c-m),min(1,c+m)]

def main():
 a=json.loads(ARCHIVE.read_text());draws=a['draws']
 need=WARMUP+TRAIN+HOLDOUT
 if len(draws)<need:raise SystemExit(f'need {need}, have {len(draws)}')
 # Context and global success tables trained strictly before holdout.
 ctx=defaultdict(lambda:defaultdict(lambda:[0,0]));glob=defaultdict(lambda:[0,0])
 for i in range(WARMUP,WARMUP+TRAIN):
  seq=[int(r['number']) for r in draws[:i]];actual=int(draws[i]['number']);key=context(seq)
  for name,fn in MODELS.items():
   hit=actual in fn(seq);ctx[key][name][0]+=int(hit);ctx[key][name][1]+=1;glob[name][0]+=int(hit);glob[name][1]+=1
 # Locked policy with empirical-Bayes shrinkage. No holdout updating.
 def choose(key):
  ranked=[]
  for name in MODELS:
   gh,gn=glob[name];prior=(gh+1)/(gn+2);ch,cn=ctx[key][name]
   score=(ch+prior*75)/(cn+75)
   ranked.append((score,cn,prior,name))
  return max(ranked)[3]
 policy={ '|'.join(k):choose(k) for k in ctx }
 results={name:[0,0] for name in MODELS};results['meta_selector']=[0,0]
 choices=Counter();records=[]
 start=WARMUP+TRAIN
 for i in range(start,start+HOLDOUT):
  seq=[int(r['number']) for r in draws[:i]];actual=int(draws[i]['number']);key=context(seq)
  preds={name:fn(seq) for name,fn in MODELS.items()}
  chosen=choose(key);choices[chosen]+=1
  for name,picks in preds.items():results[name][0]+=int(actual in picks);results[name][1]+=1
  results['meta_selector'][0]+=int(actual in preds[chosen]);results['meta_selector'][1]+=1
  if len(records)<50:records.append({'draw':int(draws[i]['draw']),'context':list(key),'chosenModel':chosen,'prediction':preds[chosen],'actual':actual,'hit':actual in preds[chosen]})
 board=[]
 for name,(h,n) in results.items():
  acc=h/n;board.append({'model':name,'tested':n,'hits':h,'misses':n-h,'accuracy':acc,'excessOverRandom':acc-BASELINE,'confidence95':wilson(h,n)})
 board.sort(key=lambda x:(-x['accuracy'],x['model']))
 payload={'version':'Meta Model Sandbox Phase 1','archiveSha256':a['sha256'],'warmup':WARMUP,'trainingDraws':TRAIN,'untouchedHoldoutDraws':HOLDOUT,'trainingStartDraw':int(draws[WARMUP]['draw']),'trainingEndDraw':int(draws[WARMUP+TRAIN-1]['draw']),'holdoutStartDraw':int(draws[start]['draw']),'holdoutEndDraw':int(draws[start+HOLDOUT-1]['draw']),'integrity':{'futureDataAccess':False,'policyLockedBeforeHoldout':True,'holdoutUpdates':False,'featuresComputedBeforeReveal':True,'selectionRule':'Context-specific hit rates shrunk toward each model global training accuracy with 75 pseudo-observations.'},'metaResult':next(x for x in board if x['model']=='meta_selector'),'bestBaseModel':next(x for x in board if x['model']!='meta_selector'),'leaderboard':board,'choiceCounts':dict(choices),'learnedContexts':len(policy),'sampleHoldoutRecords':records}
 raw=json.dumps(payload,sort_keys=True,separators=(',',':'));payload['resultSha256']=hashlib.sha256(raw.encode()).hexdigest();OUT.write_text(json.dumps(payload,indent=2));print(json.dumps({'meta':payload['metaResult'],'bestBase':payload['bestBaseModel'],'contexts':len(policy)}))
if __name__=='__main__':main()
