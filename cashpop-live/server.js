import express from "express";
import { chromium } from "playwright";

const PORT = process.env.PORT || 3000;
const URL = "https://www.michiganlottery.com/games/cash-pop?liveDraw=true";

const app = express();
app.use(express.static("public"));

let state = {
  status: "starting",
  latest: null,
  draws: [],
  candidates: [],
  signalOn: false,
  hitRate: null,
  qualifyingSignals: 0,
  missStreak: 0,
  source: null,
  lastUpdate: null
};

function uniqRecent(arr, n=5) {
  const seen = new Set(), out = [];
  for (let i = arr.length - 1; i >= 0 && out.length < n; i--) {
    const x = arr[i].value;
    if (Number.isInteger(x) && x >= 1 && x <= 15 && !seen.has(x)) {
      seen.add(x); out.push(x);
    }
  }
  return out;
}

function triggerForNext(draws) {
  if (draws.length < 4) return false;
  const a = draws.slice(-4).map(d => d.value);
  return new Set(a).size === 4;
}

function recompute() {
  const d = state.draws;
  let hits=0, sigs=0, miss=0;
  for (let i=4; i<d.length; i++) {
    const prev4 = d.slice(i-4,i).map(x=>x.value);
    if (new Set(prev4).size !== 4) continue;
    const seen = new Set(), c=[];
    for (let j=i-1; j>=0 && c.length<5; j--) {
      if (!seen.has(d[j].value)) { seen.add(d[j].value); c.push(d[j].value); }
    }
    if (c.length < 5) continue;
    sigs++;
    if (c.includes(d[i].value)) { hits++; miss=0; } else miss++;
  }
  state.qualifyingSignals=sigs;
  state.hitRate=sigs ? hits/sigs : null;
  state.missStreak=miss;
  state.signalOn=triggerForNext(d);
  state.candidates=state.signalOn ? uniqRecent(d,5) : [];
  state.latest=d.at(-1) || null;
}

function addDraw(drawNumber, value, time=null, source="network") {
  drawNumber = Number(drawNumber);
  value = Number(value);
  if (!Number.isFinite(drawNumber) || !Number.isInteger(value) || value < 1 || value > 15) return false;
  const exists = state.draws.find(x => x.drawNumber === drawNumber);
  if (exists) return false;
  state.draws.push({drawNumber, value, time});
  state.draws.sort((a,b)=>a.drawNumber-b.drawNumber);
  if (state.draws.length > 1000) state.draws = state.draws.slice(-1000);
  state.source=source;
  state.lastUpdate=new Date().toISOString();
  recompute();
  console.log("NEW DRAW", drawNumber, value, "signal:", state.signalOn, state.candidates);
  return true;
}

function inspectJSON(obj, sourceUrl) {
  const seen = new Set();
  function walk(x) {
    if (!x || typeof x !== "object" || seen.has(x)) return;
    seen.add(x);
    if (!Array.isArray(x)) {
      const keys = Object.keys(x);
      const drawKeys = keys.filter(k => /draw.*(number|no|id)|drawnumber/i.test(k));
      const valKeys = keys.filter(k => /(winning.*number|result|ball|value|winningnumber)/i.test(k));
      for (const dk of drawKeys) {
        for (const vk of valKeys) {
          const dn = Number(x[dk]);
          const valRaw = x[vk];
          const vals = Array.isArray(valRaw) ? valRaw : [valRaw];
          for (const vv of vals) {
            const val = Number(typeof vv === "object" && vv ? (vv.value ?? vv.number ?? vv.result) : vv);
            if (dn > 10000 && val >= 1 && val <= 15) addDraw(dn, val, x.time ?? x.drawTime ?? x.timestamp ?? null, sourceUrl);
          }
        }
      }
    }
    for (const v of Object.values(x)) walk(v);
  }
  walk(obj);
}

async function scrapeDOM(page) {
  const txt = await page.locator("body").innerText().catch(()=> "");
  const m = txt.match(/(?:Current\s+Draw|Draw)\s*#?\s*(\d{5,})/i);
  if (!m) return;
  const drawNumber = Number(m[1]);
  const selectors = [
    "[class*='winning']","[class*='result']","[class*='ball']",
    "[aria-label*='winning' i]","[data-testid*='result' i]"
  ];
  for (const sel of selectors) {
    const els = await page.locator(sel).allTextContents().catch(()=>[]);
    for (const t of els) {
      const mm=t.match(/\b(1[0-5]|[1-9])\b/);
      if (mm) addDraw(drawNumber, Number(mm[1]), null, "DOM:"+sel);
    }
  }
}

async function run() {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({
    userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1"
  });

  page.on("response", async (res) => {
    try {
      const ct=(res.headers()["content-type"]||"").toLowerCase();
      if (!ct.includes("json")) return;
      const data=await res.json();
      inspectJSON(data, res.url());
    } catch {}
  });

  state.status="opening official live page";
  await page.goto(URL, {waitUntil:"domcontentloaded", timeout:60000});
  state.status="watching";

  setInterval(()=>scrapeDOM(page).catch(()=>{}), 10000);
  setInterval(async ()=>{
    if (!state.lastUpdate || Date.now()-Date.parse(state.lastUpdate)>8*60*1000) {
      await page.reload({waitUntil:"domcontentloaded",timeout:60000}).catch(()=>{});
    }
  }, 45000);
}

app.get("/api/state", (req,res)=>res.json(state));
app.get("/health", (req,res)=>res.json({ok:true,status:state.status,lastUpdate:state.lastUpdate}));

app.listen(PORT, ()=>{
  console.log("Dashboard: http://localhost:"+PORT);
  run().catch(err=>{state.status="error: "+err.message; console.error(err);});
});
