#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path
STATE=Path('v0/cloud_state.json'); OUT=Path('research/data_integrity_audit.json')
st=json.loads(STATE.read_text()); rows=st.get('draws',[])
parsed=[]
for r in rows:
    try: parsed.append({'draw':int(r['draw']),'number':int(r['number']),'date':r.get('date'),'time':r.get('time'),'source':r.get('source')})
    except Exception: pass
parsed.sort(key=lambda x:x['draw'])
ids=[r['draw'] for r in parsed]
nums=[r['number'] for r in parsed]
dups=[k for k,v in Counter(ids).items() if v>1]
missing=[]
if ids:
    present=set(ids)
    missing=[x for x in range(ids[0],ids[-1]+1) if x not in present]
sources=Counter(str(r.get('source')) for r in parsed)
out={
 'rowsRaw':len(rows),'rowsParsed':len(parsed),'uniqueDraws':len(set(ids)),
 'firstDraw':ids[0] if ids else None,'lastDraw':ids[-1] if ids else None,
 'nominalSpan':(ids[-1]-ids[0]+1) if ids else 0,
 'duplicateDrawIds':dups,'duplicateCount':len(dups),
 'missingDrawIds':missing,'missingCount':len(missing),
 'invalidWinningNumbers':[{'draw':r['draw'],'number':r['number']} for r in parsed if not 1<=r['number']<=15],
 'sources':dict(sources),
 'firstRecord':parsed[0] if parsed else None,'lastRecord':parsed[-1] if parsed else None,
 'conclusion':'NOT_THOUSANDS' if len(set(ids))<2000 else 'THOUSANDS_AVAILABLE'
}
OUT.write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
