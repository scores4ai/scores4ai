#!/usr/bin/env python3
import json, math, os, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URL = "https://cash-pop.com/michigan/winning-numbers"
N8N_FEED_URL = os.getenv("N8N_FEED_URL", "").strip()
STATE_PATH = Path(__file__).with_name("cloud_state.json")
MAX_DRAWS = 600
MODEL_IDS = [
    "overall","recent24","recent60","decay92","decay97","markov1","markov2",
    "lag7","lag8","cycle8","cycle15","cycle24","similarity4","similarity6","antiRepeat"
]
MODEL_NAMES = {
    "overall":"Overall frequency","recent24":"Recent 24","recent60":"Recent 60",
    "decay92":"Decay 0.92","decay97":"Decay 0.97","markov1":"Markov 1",
    "markov2":"Markov 2","lag7":"Lag 7","lag8":"Lag 8","cycle8":"Cycle 8",
    "cycle15":"Cycle 15","cycle24":"Cycle 24","similarity4":"Similarity 4",
    "similarity6":"Similarity 6","antiRepeat":"Anti-repeat"
}

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def fetch_url(url):
    req = Request(url, headers={"User-Agent":"Mozilla/5.0 CashPopResearchBot/2.0","Accept":"application/json,text/html,*/*"})
    with urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8","ignore"), r.headers.get("content-type","")

def strip_html(html):
    html = re.sub(r"<script[\s\S]*?</script>", "\n", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", "\n", html, flags=re.I)
    html = re.sub(r"<(?:br|/p|/div|/li|/h[1-6]|/tr)[^>]*>", "\n", html, flags=re.I)
    text = re.sub(r"<[^>]+>", "\n", html)
    text = (text.replace("&nbsp;"," ").replace("&amp;","&").replace("&ndash;","–").replace("&mdash;","—"))
    text = re.sub(r"[ \t]+"," ",text)
    return re.sub(r"\n{2,}","\n",text).strip()

def parse_html_draws(html):
    text = strip_html(html)
    dates = list(re.finditer(r"(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}", text))
    out = {}
    for i, dm in enumerate(dates):
        date_label = dm.group(0)
        block = text[dm.end():(dates[i+1].start() if i+1 < len(dates) else len(text))]
        rx = re.compile(r"(?:^|\n)\s*(1[0-5]|[1-9])\s*\n+\s*#(\d{4,})\s*\n+\s*(\d{1,2}:\d{2}\s*(?:AM|PM))\b", re.I)
        for m in rx.finditer(block):
            draw = int(m.group(2))
            out[draw] = {"draw":draw,"number":int(m.group(1)),"date":date_label,
                         "time":re.sub(r"\s+"," ",m.group(3)).upper(),"source":"cash-pop.com"}
    return [out[k] for k in sorted(out)]

def parse_json_draws(payload):
    rows = payload if isinstance(payload,list) else payload.get("results") or payload.get("data") or []
    out = {}
    for x in rows:
        try:
            draw = int(x.get("drawNumber",x.get("draw",x.get("draw_number"))))
            number = int(x.get("winningNumber",x.get("number",x.get("result"))))
        except Exception:
            continue
        if draw > 0 and 1 <= number <= 15:
            out[draw] = {"draw":draw,"number":number,"date":str(x.get("date","")),
                         "time":str(x.get("time",x.get("timestamp",""))),"source":"n8n"}
    return [out[k] for k in sorted(out)]

def fetch_draws():
    errors = []
    if N8N_FEED_URL:
        try:
            body, _ = fetch_url(N8N_FEED_URL)
            rows = parse_json_draws(json.loads(body))
            if rows:
                return rows, "n8n"
        except Exception as e:
            errors.append(f"n8n: {e}")
    try:
        body, _ = fetch_url(SOURCE_URL)
        rows = parse_html_draws(body)
        if rows:
            return rows, "cash-pop.com fallback"
    except Exception as e:
        errors.append(f"source: {e}")
    raise RuntimeError("No draw feed available: " + "; ".join(errors))

def norm(a):
    s = sum(a) or 1.0
    return [x/s for x in a]

def count_model(seq,start):
    a=[0.5]*15
    for x in seq[start:]: a[x-1]+=1
    return norm(a)

def decay_model(seq,decay):
    a=[0.4]*15
    w=1.0
    for x in reversed(seq):
        a[x-1]+=w; w*=decay
    return norm(a)

def markov_model(seq,order):
    a=[0.4]*15
    if len(seq)<=order: return norm(a)
    target=seq[-order:]
    for i in range(order,len(seq)):
        if seq[i-order:i]==target: a[seq[i]-1]+=1
    return norm(a)

def lag_model(seq,lag):
    a=[0.5]*15
    if len(seq)>=lag: a[seq[-lag]-1]+=4
    return norm(a)

def cycle_model(seq,cycle):
    a=[0.5]*15; slot=len(seq)%cycle
    for i,x in enumerate(seq):
        if i%cycle==slot: a[x-1]+=1
    return norm(a)

def similarity_model(seq,length):
    a=[0.5]*15
    if len(seq)<=length: return norm(a)
    target=seq[-length:]; candidates=[]
    for end in range(length,len(seq)):
        d=sum(seq[end-length+j]!=target[j] for j in range(length))
        candidates.append((d,seq[end]))
    candidates.sort()
    for i,(d,nxt) in enumerate(candidates[:18]):
        a[nxt-1]+=1/(1+d+i*0.08)
    return norm(a)

def anti_repeat_model(seq):
    a=[1.0]*15
    if seq: a[seq[-1]-1]=0.12
    return norm(a)

def model_rows(seq):
    specs = [
        ("overall",count_model(seq,0)),("recent24",count_model(seq,max(0,len(seq)-24))),
        ("recent60",count_model(seq,max(0,len(seq)-60))),("decay92",decay_model(seq,.92)),
        ("decay97",decay_model(seq,.97)),("markov1",markov_model(seq,1)),
        ("markov2",markov_model(seq,2)),("lag7",lag_model(seq,7)),("lag8",lag_model(seq,8)),
        ("cycle8",cycle_model(seq,8)),("cycle15",cycle_model(seq,15)),
        ("cycle24",cycle_model(seq,24)),("similarity4",similarity_model(seq,4)),
        ("similarity6",similarity_model(seq,6)),("antiRepeat",anti_repeat_model(seq))
    ]
    return [{"id":mid,"name":MODEL_NAMES[mid],"scores":scores} for mid,scores in specs]

def rank5(scores):
    return [i+1 for i,_ in sorted(enumerate(scores),key=lambda z:(-z[1],z[0]))[:5]]

def fresh_weights():
    return {mid:1.0 for mid in MODEL_IDS}

def predict(seq,weights):
    combined=[0.0]*15; rows=model_rows(seq)
    for m in rows:
        m["top5"]=rank5(m["scores"])
        m["weight"]=max(.05,float(weights.get(m["id"],1)))
        for i,s in enumerate(m["scores"]): combined[i]+=s*m["weight"]
    return rank5(combined),rows

def update_weights(weights,rows,actual):
    for m in rows:
        cur=float(weights.get(m["id"],1))
        hit=actual in m["top5"]
        weights[m["id"]]=max(.05,min(20,cur*(1.075 if hit else .965)))
    avg=sum(weights.values())/len(weights)
    for k in weights: weights[k]/=avg

def replay(draws):
    seq=[]; weights=fresh_weights(); history=[]
    warmup=min(60,max(30,int(len(draws)*.10)))
    for row in draws:
        if len(seq)>=warmup:
            picks,rows=predict(seq,weights)
            history.append({"draw":row["draw"],"top5":picks,"actual":row["number"],
                            "hit5":row["number"] in picks,
                            "modelResults":{m["id"]:row["number"] in m["top5"] for m in rows},
                            "type":"historical_walk_forward"})
            update_weights(weights,rows,row["number"])
        seq.append(row["number"])
    return history,weights,warmup

def summarize(history):
    success=sum(1 for x in history if x.get("hit5"))
    live=[x for x in history if x.get("type")=="automated_future_test"]
    live_success=sum(1 for x in live if x.get("hit5"))
    return {"evaluated":len(history),"successes":success,"misses":len(history)-success,
            "accuracy":success/len(history) if history else 0,
            "liveEvaluated":len(live),"liveSuccesses":live_success,
            "liveMisses":len(live)-live_success,
            "liveAccuracy":live_success/len(live) if live else 0,
            "randomTop5Baseline":1/3}

def load_state():
    if STATE_PATH.exists():
        try: return json.loads(STATE_PATH.read_text())
        except Exception: pass
    return {"draws":[],"history":[],"weights":fresh_weights(),"pending":None}

def main():
    state=load_state()
    fetched,feed_name=fetch_draws()
    existing={int(x["draw"]):x for x in state.get("draws",[])}
    for r in fetched: existing[r["draw"]]=r
    all_draws=[existing[k] for k in sorted(existing)][-MAX_DRAWS:]

    previous_draws={int(x["draw"]):x for x in state.get("draws",[])}
    new_rows=[r for r in all_draws if r["draw"] not in previous_draws]
    pending=state.get("pending")
    live_history=[x for x in state.get("history",[]) if x.get("type")=="automated_future_test"]

    historical,weights,warmup=replay(all_draws)
    seq=[x["number"] for x in all_draws]

    for row in sorted(new_rows,key=lambda x:x["draw"]):
        if pending and int(pending.get("draw",-1))==row["draw"]:
            model_top5=pending.get("modelTop5",{})
            live_history.append({"draw":row["draw"],"top5":pending["top5"],"actual":row["number"],
                "hit5":row["number"] in pending["top5"],
                "modelResults":{mid:row["number"] in model_top5.get(mid,[]) for mid in MODEL_IDS},
                "type":"automated_future_test","predictedAt":pending.get("createdAt"),"scoredAt":utcnow()})

    picks,rows=predict(seq,weights)
    next_draw=(max((x["draw"] for x in all_draws),default=0)+1)
    pending={"draw":next_draw,"top5":picks,"modelTop5":{m["id"]:m["top5"] for m in rows},
             "createdAt":utcnow(),"feedControlled":True}
    merged_history=historical+live_history
    state={"draws":all_draws,"history":merged_history,"weights":weights,"pending":pending,
           "warmup":warmup,"stats":summarize(merged_history),"latestDraw":next_draw-1,
           "seedCount":len(all_draws),"feed":feed_name,"source":N8N_FEED_URL or SOURCE_URL,
           "updatedAt":utcnow(),"modelNames":MODEL_NAMES}
    STATE_PATH.write_text(json.dumps(state,indent=2))

if __name__=="__main__":
    main()
