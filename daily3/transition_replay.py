#!/usr/bin/env python3
import hashlib,json
from collections import Counter,defaultdict
from pathlib import Path

ARCHIVE=Path('daily3/archive.json')
BASE=Path('daily3/baseline_results.json')
OUT=Path('daily3/transition_results.json')
WARMUP=200


def predict(history):
    prev=history[-1]['digits']
    out=[]
    for p in range(3):
        c=Counter()
        for a,b in zip(history,history[1:]):
            if int(a['digits'][p])==int(prev[p]): c[int(b['digits'][p])]+=1
        if c: out.append(c.most_common(1)[0][0])
        else: out.append(Counter(int(r['digits'][p]) for r in history).most_common(1)[0][0])
    return out


def score(pred,actual,s):
    hits=[pred[i]==actual[i] for i in range(3)]
    s['tested']+=1;s['exactHits']+=int(all(hits));s['atLeastOnePositionHits']+=int(any(hits))
    for i,h in enumerate(hits):s['positionHits'][i]+=int(h)


def main():
    a=json.loads(ARCHIVE.read_text());draws=a['draws']
    s={'tested':0,'exactHits':0,'atLeastOnePositionHits':0,'positionHits':[0,0,0]};samples=[]
    for i in range(WARMUP,len(draws)):
        history=draws[:i];pred=predict(history);actual=[int(x) for x in draws[i]['digits']]
        fp=hashlib.sha256(json.dumps({'target':draws[i]['sequence'],'prediction':pred},sort_keys=True).encode()).hexdigest()
        score(pred,actual,s)
        if len(samples)<25:samples.append({'sequence':draws[i]['sequence'],'knownThrough':history[-1]['sequence'],'prediction':pred,'actual':actual,'fingerprint':fp})
    n=s['tested'];result={'model':'position_transition_1','tested':n,'exactHits':s['exactHits'],'exactAccuracy':s['exactHits']/n,'atLeastOnePositionHits':s['atLeastOnePositionHits'],'atLeastOnePositionAccuracy':s['atLeastOnePositionHits']/n,'positionHits':s['positionHits'],'positionAccuracy':[x/n for x in s['positionHits']]}
    baselines=json.loads(BASE.read_text())['results']
    out={'version':'Daily 3 Transition Replay Phase 1','archiveSha256':a['sha256'],'warmupDraws':WARMUP,'integrity':{'futureDataAccess':False,'predictionsFrozenBeforeReveal':True},'transitionResult':result,'baselineResults':baselines,'beatBestBaselineExact':result['exactHits']>max(x['exactHits'] for x in baselines),'samples':samples}
    raw=json.dumps(out,sort_keys=True,separators=(',',':'));out['resultSha256']=hashlib.sha256(raw.encode()).hexdigest();OUT.write_text(json.dumps(out,indent=2));print(json.dumps(result))

if __name__=='__main__':main()
