import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import { blip, buzz, sfx } from "../lib/sound";
import DATA from "./paths.json";

interface RideData { id: string; code: string; name: string; dates: string[]; close: number[] }
const RIDES: RideData[] = (DATA as { rides: RideData[] }).rides;
const CAP = 20;
const LEAD = 30;
const RIDE_SEC = 11;
const W = 340;
const H = 176;
const LANES = [10, 30, 50, 70];

const POOLS: Record<string, string[]> = {
  hot: ["满仓！", "这次不一样", "楼下大妈都在聊股票", "目标一万点", "借钱也要上", "闭眼买都赚", "辞职炒股了", "还能再翻一倍"],
  up: ["又红了", "早知道多买点", "拿住别动", "回调就是机会", "冲冲冲", "今天吃肉"],
  down: ["跌了跌了", "要不要跑？", "只是回调吧", "补仓还是割肉？", "心慌", "别慌，长期持有"],
  fear: ["割了割了", "再也不碰股票了", "抄底抄在半山腰", "装死", "一夜回到解放前", "卸载软件了"],
  flat: ["横盘好无聊", "等一个信号", "观望观望", "今天没啥行情"],
  goneUp: ["卖飞了吧", "下车的人哭了", "早知道拿着"],
  goneDown: ["跑得好！", "还好下车了", "高手"],
};

const pick = <T,>(a: T[]) => a[Math.floor(Math.random() * a.length)];
const pctTxt = (x: number) => `${Math.round(Math.abs(x) * 100)}%`;
const ym = (d: string) => `${d.slice(0, 4)}.${Number(d.slice(5, 7))}`;
const wan = (x: number) => x.toFixed(1);

function mood(c: number[], i: number) {
  const seen = c.slice(0, i + 1);
  const hi = Math.max(...seen);
  const lo = Math.min(...seen);
  const back = c[Math.max(0, i - 10)];
  if (c[i] / hi - 1 < -0.2) return "fear";
  if (c[i] >= hi * 0.98 && c[i] / lo > 1.4) return "hot";
  if (c[i] / back - 1 > 0.04) return "up";
  if (c[i] / back - 1 < -0.04) return "down";
  return "flat";
}

function verdict(c: number[], entry: number, exit: number, forced: boolean) {
  const e = c[entry];
  const x = c[exit];
  const gain = x / e - 1;
  const peak = Math.max(...c.slice(entry, exit + 1));
  const rest = c.slice(exit);
  const maxAfter = Math.max(...rest);
  const minAfter = Math.min(...rest);
  if (exit - entry < 4) return { t: "手比脑子快", sub: "刚买就卖了", good: null };
  if (!forced && x >= Math.max(...c) * 0.93) return { t: "逃顶高手", sub: "卖在了离最高点不远的地方", good: true };
  if (gain > 0 && peak > x * 1.4) return { t: "坐了趟过山车", sub: "浮盈坐上去，又坐下来", good: null };
  if (gain > 0 && maxAfter > x * 1.25) return { t: "卖飞了", sub: "下车太早，后面还有一大段", good: null };
  if (gain > 0) return { t: "落袋为安", sub: "赚到就走", good: true };
  if (peak > e * 1.2) return { t: "坐了趟过山车", sub: "赚过不少，最后还亏了", good: false };
  if (maxAfter > x * 1.15) return { t: "割在地板", sub: "刚卖完，它就涨回去了", good: false };
  if (minAfter < x * 0.88) return { t: "及时止损", sub: "卖完它还在跌", good: true };
  return { t: "小亏离场", sub: "没赚到，也没伤筋动骨", good: false };
}

function afterText(c: number[], exit: number, forced: boolean) {
  if (forced) return "一直拿到了最后";
  const x = c[exit];
  const rest = c.slice(exit);
  const iMax = rest.indexOf(Math.max(...rest));
  const iMin = rest.indexOf(Math.min(...rest));
  const up = rest[iMax] / x - 1;
  const dn = rest[iMin] / x - 1;
  if (up > 0.05 && (iMax < iMin || dn > -0.05)) {
    const fall = 1 - Math.min(...rest.slice(iMax)) / rest[iMax];
    return `下车后又涨了 ${pctTxt(up)}${fall > 0.1 ? `，再跌掉 ${pctTxt(fall)}` : ""}`;
  }
  if (dn < -0.05) {
    const reb = Math.max(...rest.slice(iMin)) / rest[iMin] - 1;
    return `下车后跌了 ${pctTxt(dn)}${reb > 0.1 ? `，又反弹 ${pctTxt(reb)}` : ""}`;
  }
  return "下车后它没怎么动";
}

function revealText(r: RideData) {
  const c = r.close;
  const iMax = c.indexOf(Math.max(...c));
  const end = c[c.length - 1];
  return { when: `${ym(r.dates[0])}—${ym(r.dates[r.dates.length - 1])} · ${r.name}`, path: `${Math.round(c[0])} → ${Math.round(c[iMax])} → ${Math.round(end)} 点` };
}

type Phase = "idle" | "ride" | "after" | "done";
interface Bullet { id: number; text: string; top: number }

/** 首页热身：按住 = 满仓买入，松手 = 全部卖出，只能进出一次 */
export function Ride() {
  const [ri, setRi] = useState(() => Number(sessionStorage.getItem("ts-ride-i") || 0) % RIDES.length);
  const r = RIDES[ri];
  const c = r.close;
  const len = c.length;
  const [phase, setPhase] = useState<Phase>("idle");
  const [head, setHead] = useState(LEAD);
  const [entry, setEntry] = useState<number | null>(null);
  const [exit, setExit] = useState<number | null>(null);
  const [forced, setForced] = useState(false);
  const [bullets, setBullets] = useState<Bullet[]>([]);
  const [shake, setShake] = useState(0);
  const [toast, setToast] = useState<string | null>(null);
  const headRef = useRef(LEAD);
  const phaseRef = useRef<Phase>("idle");
  const entryRef = useRef<number | null>(null);
  const exitRef = useRef<number | null>(null);
  const marks = useRef(new Set<number>());
  const lastHead = useRef(LEAD);
  const lastBlip = useRef(LEAD);
  const bid = useRef(0);
  const scale = useRef({ lo: 0, hi: 0 });
  const [best, setBest] = useState<{ p: number } | null>(() => {
    try {
      return JSON.parse(localStorage.getItem("ts-ride-best") || "null");
    } catch {
      return null;
    }
  });

  phaseRef.current = phase;

  function reset(next: number) {
    phaseRef.current = "idle";
    sessionStorage.setItem("ts-ride-i", String(next));
    setRi(next);
    setPhase("idle");
    setHead(LEAD);
    headRef.current = LEAD;
    setEntry(null);
    setExit(null);
    entryRef.current = null;
    exitRef.current = null;
    setForced(false);
    setBullets([]);
    marks.current.clear();
    scale.current = { lo: 0, hi: 0 };
  }

  function press() {
    if (phaseRef.current !== "idle") return;
    const at = Math.floor(headRef.current);
    entryRef.current = at;
    lastHead.current = at;
    lastBlip.current = at;
    phaseRef.current = "ride";
    setEntry(at);
    setPhase("ride");
    sfx.tap();
    buzz(20);
  }

  function release(end = false) {
    if (phaseRef.current !== "ride") return;
    const at = Math.min(len - 1, Math.floor(headRef.current));
    const next: Phase = at >= len - 1 ? "done" : "after";
    phaseRef.current = next;
    exitRef.current = at;
    setExit(at);
    setForced(end);
    const gain = c[at] / c[entryRef.current!] - 1;
    gain >= 0 ? sfx.coin() : sfx.loss();
    buzz(gain >= 0 ? [20, 30, 40] : 60);
    setPhase(next);
  }

  useEffect(() => {
    if (phase !== "ride" && phase !== "after") return;
    let raf = 0;
    let last = performance.now();
    let since = 0;
    const speed = ((len - LEAD) / RIDE_SEC) * (phase === "after" ? 3 : 1);
    const loop = (now: number) => {
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      headRef.current = Math.min(len - 1, headRef.current + dt * speed);
      const h = Math.floor(headRef.current);
      setHead((p) => (p === h ? p : h));
      since += dt;
      if (since > 0.8) {
        since = 0;
        const pool = phase === "after" ? (c[h] >= c[exitRef.current!] ? "goneUp" : "goneDown") : mood(c, h);
        const id = ++bid.current;
        setBullets((b) => [...b.slice(-5), { id, text: pick(POOLS[pool]), top: LANES[id % LANES.length] }]);
      }
      if (h >= len - 1) {
        if (phase === "ride") release(true);
        else setPhase("done");
        return;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [phase, ri]);

  useEffect(() => {
    if (phase !== "ride" || entry == null) return;
    const g = c[head] / c[entry] - 1;
    const step = Math.max(1, Math.round((len - LEAD) / RIDE_SEC / 9));
    if (head - lastBlip.current >= step) {
      lastBlip.current = head;
      blip(c[head] / c[entry]);
    }
    let crash = false;
    for (let k = lastHead.current + 1; k <= head; k++) if (k > 0 && c[k] / c[k - 1] - 1 < -0.04) crash = true;
    lastHead.current = head;
    if (crash) {
      sfx.thud();
      buzz(30);
      setShake((s) => s + 1);
    }
    for (const [m, txt] of [[0.5, "赚了五成！"], [1, "翻倍了！"], [2, "翻了两番！"]] as [number, string][]) {
      if (g >= m && !marks.current.has(m)) {
        marks.current.add(m);
        sfx.gain();
        buzz([15, 30, 15]);
        setToast(txt);
        setTimeout(() => setToast(null), 1100);
      }
    }
  }, [head]);

  useEffect(() => {
    if (phase !== "done" || entry == null || exit == null) return;
    const p = c[exit] / c[entry] - 1;
    if (!best || p > best.p) {
      const b = { p };
      localStorage.setItem("ts-ride-best", JSON.stringify(b));
      setBest(b);
    }
  }, [phase]);

  const view = useMemo(() => {
    const seen = c.slice(0, head + 1);
    let lo = Math.min(...seen);
    let hi = Math.max(...seen);
    const pad = (hi - lo) * 0.12 || hi * 0.05;
    lo -= pad;
    hi += pad;
    const s = scale.current;
    s.lo = s.lo ? s.lo + (lo - s.lo) * 0.35 : lo;
    s.hi = s.hi ? s.hi + (hi - s.hi) * 0.35 : hi;
    const span = Math.max(head * 1.06, 60);
    const X = (i: number) => (i / span) * W;
    const Y = (v: number) => H - ((v - s.lo) / (s.hi - s.lo)) * H;
    const line = (a: number, b: number) => c.slice(a, b + 1).map((v, k) => `${k ? "L" : "M"}${X(a + k).toFixed(1)},${Y(v).toFixed(1)}`).join("");
    const cut = exit ?? head;
    return { X, Y, main: line(0, Math.min(cut, head)), ghost: exit != null && head > exit ? line(exit, head) : "" };
  }, [head, ri, exit]);

  const now = c[head];
  const base = entry != null ? c[entry] : now;
  const sellAt = exit != null ? c[exit] : null;
  const value = entry == null ? CAP : CAP * ((sellAt ?? now) / base);
  const gain = value / CAP - 1;
  const cls = gain > 0.0005 ? "up" : gain < -0.0005 ? "down" : "";
  const glow = entry == null ? 0 : Math.min(1, Math.abs(gain));
  const v = phase === "done" && entry != null && exit != null ? verdict(c, entry, exit, forced) : null;
  const rv = revealText(r);

  return (
    <div className="ride">
      <div className="row between">
        <div className="kicker">热身 · 按住坐一趟真实行情</div>
        {best && <span className="tiny bold">最好 {best.p >= 0 ? "+" : "−"}{Math.round(Math.abs(best.p) * 100)}%</span>}
      </div>
      <motion.div className="ride-chart mt8" animate={shake ? { x: [0, -7, 7, -4, 4, 0] } : undefined} key={shake}
        style={{ background: `radial-gradient(circle at 75% 25%, ${gain >= 0 ? `rgba(212,67,42,${glow * 0.38})` : `rgba(60,122,78,${glow * 0.45})`}, transparent 62%), #FFFBF1` }}>
        <div className="ride-acct">
          <span className="tiny bold">{entry == null ? "本金 · 空仓" : exit != null ? "已全部卖出" : "满仓 · 总资产"}</span>
          <b className={"num " + cls}>{wan(value)}<small> 万</small></b>
          {entry != null && <span className={"bold " + cls}>{gain >= 0 ? "+" : "−"}{(Math.abs(gain) * 100).toFixed(1)}%</span>}
        </div>
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="none" style={{ display: "block", overflow: "visible" }}>
          {entry != null && <line x1={0} x2={W} y1={view.Y(c[entry])} y2={view.Y(c[entry])} stroke="#77745A" strokeDasharray="4 4" strokeWidth={1} />}
          {view.ghost && <path d={view.ghost} fill="none" stroke="#A9A48A" strokeWidth={2} strokeDasharray="3 3" />}
          <path d={view.main} fill="none" stroke={entry == null ? "#2A2A1C" : gain >= 0 ? "#D4432A" : "#3C7A4E"} strokeWidth={2.4} strokeLinejoin="round" />
          {entry != null && <g><circle cx={view.X(entry)} cy={view.Y(c[entry])} r={8} fill="#D4432A" stroke="#2A2A1C" strokeWidth={1.5} /><text x={view.X(entry)} y={view.Y(c[entry]) + 3.5} fontSize={9} fontWeight={900} textAnchor="middle" fill="#fff">买</text></g>}
          {exit != null && <g><circle cx={view.X(exit)} cy={view.Y(c[exit])} r={8} fill="#2D5F6B" stroke="#2A2A1C" strokeWidth={1.5} /><text x={view.X(exit)} y={view.Y(c[exit]) + 3.5} fontSize={9} fontWeight={900} textAnchor="middle" fill="#fff">卖</text></g>}
          <circle cx={view.X(head)} cy={view.Y(now)} r={phase === "ride" ? 5 : 4} fill={phase === "ride" ? "#F3D27F" : "#2A2A1C"} stroke="#2A2A1C" strokeWidth={1.5} />
        </svg>
        <div className="ride-bullets">
          <AnimatePresence>
            {bullets.map((b) => (
              <motion.span key={b.id} className="ride-bullet" style={{ top: `${b.top}%` }} initial={{ x: 360, opacity: 0 }} animate={{ x: -260, opacity: [0, 1, 1, 0] }} transition={{ duration: 4.2, ease: "linear" }}
                onAnimationComplete={() => setBullets((xs) => xs.filter((x) => x.id !== b.id))}>{b.text}</motion.span>
            ))}
          </AnimatePresence>
        </div>
        <AnimatePresence>{toast && <motion.div className="ride-toast" initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ opacity: 0, y: -20 }}>{toast}</motion.div>}</AnimatePresence>
        <div className="ride-date tiny">{phase === "done" ? r.dates[head] : "日期已隐藏"}</div>
        {phase !== "idle" && <span className="crowd-tag" style={{ left: 8, bottom: 6 }}>弹幕为虚构的散户声音</span>}
      </motion.div>

      {phase !== "done" ? (
        <div className="row gap12 mt12" style={{ alignItems: "center" }}>
          <button className={"ride-btn" + (phase === "ride" ? " on" : "")} disabled={phase === "after"}
            onPointerDown={(e) => { e.preventDefault(); e.currentTarget.setPointerCapture?.(e.pointerId); press(); }}
            onPointerUp={() => release()} onPointerCancel={() => release()} onLostPointerCapture={() => release()} onContextMenu={(e) => e.preventDefault()}>
            {phase === "idle" ? "按住\n买入" : phase === "ride" ? "松手\n卖出" : "…"}
          </button>
          <div className="small" style={{ lineHeight: 1.5 }}>
            {phase === "idle" ? <><b>20 万本金</b><br />按住买入，松手卖出。只有一次。</> : phase === "ride" ? <b>拿住，还是走？</b> : <b>看看你下车以后……</b>}
          </div>
        </div>
      ) : v && (
        <motion.div className="mt12" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <div className="row gap10" style={{ alignItems: "center" }}>
            <motion.span className={"ride-stamp " + (v.good === true ? "good" : v.good === false ? "bad" : "")} initial={{ scale: 2.4, rotate: -14, opacity: 0 }} animate={{ scale: 1, rotate: -6, opacity: 1 }} transition={{ type: "spring", stiffness: 380, damping: 16 }}>{v.t}</motion.span>
            <div>
              <div className="bold">{v.sub}</div>
              <div className="small">最高 {wan(CAP * Math.max(...c.slice(entry!, exit! + 1)) / c[entry!])} 万 · {afterText(c, exit!, forced)}</div>
            </div>
          </div>
          <div className="ride-reveal mt8">
            <span className="tiny bold">原来是 {rv.when}</span>
            <b className="display num">{rv.path}</b>
            <span className="tiny">真实收盘价 · Panda Data 指数日线</span>
          </div>
          <button className="btn sm block mt8" onClick={() => { sfx.tap(); reset((ri + 1) % RIDES.length); }}>再坐一次 · 换一段行情</button>
        </motion.div>
      )}
    </div>
  );
}
