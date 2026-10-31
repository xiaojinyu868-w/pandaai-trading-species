import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import { blip, buzz, sfx } from "../lib/sound";
import { ticksOf, type Level } from "./levels";
import { ART } from "../data";
import { sp } from "../game/meta";

export const CAP = 20;
const W = 340;
const H = 210;

export interface Trade { k: "buy" | "sell"; i: number; day: number; p: number; ms: number; why?: "start" | "liq" | "end" | "lock" | "resume" }
export interface Run {
  id: string;
  eq: number;
  peak: number;
  low: number;
  trades: Trade[];
  /** 持有时间占整段的比例 */
  held: number;
  /** 第一次按下距开局多少毫秒（开局就拿着的关不算） */
  firstMs: number | null;
  lev: number;
  levAt?: number;
  liq: boolean;
  lockTries: number;
  holidayHeld?: boolean;
  openAct?: "buy" | "sell" | "hold" | "none";
  /** 抱团圈：你走的时候已经走了几个人；-1 = 见顶前就走了；null = 没走 */
  leftRank?: number | null;
  crowdLeft?: number;
  haltSold?: number;
  panicBuy?: boolean;
  /** 这一场的本金（万）；四季连着玩时是棋盘上的资金 */
  cap?: number;
  plan?: Plan;
  planTriggered?: boolean;
  planFollowed?: boolean | null;
}

export type Plan = "cut" | "add" | "none";
/** AI 对手按桌游里自己的牌出手：在第 i 个点买或卖 */
export interface Foe { id: string; trades: { i: number; k: "buy" | "sell" }[] }

type Phase = "ready" | "count" | "run" | "pause" | "end";
type Pause = null | { k: "holiday" } | { k: "offer" } | { k: "halt"; n: number } | { k: "liq" };
interface Bullet { id: number; text: string; top: number }
const LANES = [8, 26, 44, 62];
const pick = <T,>(a: T[]) => a[Math.floor(Math.random() * a.length)];
const wan = (x: number) => (Math.abs(x) >= 100 ? x.toFixed(0) : x.toFixed(1));

export function Game({ level, onDone, cap = CAP, plan = "none", foes = [], noMax = false }: { level: Level; onDone: (r: Run) => void; cap?: number; plan?: Plan; foes?: Foe[]; noMax?: boolean }) {
  const T = useMemo(() => ticksOf(level), [level.id]);
  const floor = level.lev ? (level.lev.floor * cap) / CAP : 0;
  const N = T.p.length;
  const dayTick = (d: string, which: "open" | "close") => {
    const i = T.dates.indexOf(d);
    return i < 0 ? -1 : i * 2 + (which === "close" ? 1 : 0);
  };
  const ev = useMemo(() => {
    const slowAt = new Float32Array(N).fill(1);
    level.slow.forEach(([a, b, f]) => {
      const i = Math.max(0, dayTick(a, "open"));
      const j = dayTick(b, "close");
      for (let k = i; k <= (j < 0 ? N - 1 : j); k++) slowAt[k] = f;
    });
    let cost = 0;
    for (let k = 0; k < N; k++) cost += 1 / slowAt[k];
    const lockDays = new Set((level.lock || []).map((d) => T.dates.indexOf(d)).filter((i) => i >= 0));
    const halts = (level.halts || []).map((d) => dayTick(d, "close")).filter((i) => i >= 0);
    const hol = level.holiday ? dayTick(level.holiday.close, "close") : -1;
    let peakI = 0;
    T.p.forEach((v, k) => v > T.p[peakI] && (peakI = k));
    return { slowAt, base: cost / level.sec, lockDays, halts, hol, peakI, peak: T.p[peakI] };
  }, [level.id]);

  const [phase, setPhase] = useState<Phase>("ready");
  const [pause, setPause] = useState<Pause>(null);
  const [count, setCount] = useState(3);
  const [waitHold, setWaitHold] = useState(false);
  const [head, setHead] = useState(0);
  const [finger, setFinger] = useState(false);
  const [bullets, setBullets] = useState<Bullet[]>([]);
  const [toast, setToast] = useState<{ t: string; tone?: "up" | "down" | "dark" } | null>(null);
  const [shake, setShake] = useState(0);
  const [, force] = useState(0);
  const bump = () => force((x) => x + 1);

  const S = useRef({
    head: 0, finger: false, phase: "ready" as Phase,
    cash: cap, shares: 0, debt: 0, levSet: 1, levMax: 1, levAt: undefined as number | undefined,
    planAt: -1, planTriggered: false, planFollowed: null as boolean | null,
    trades: [] as Trade[], t0: 0, firstMs: null as number | null, heldT: 0, runT: 0,
    peak: cap, low: cap, liq: false, lockTries: 0, locked: false, pendingLock: false,
    offered: false, haltsDone: 0, holidayDone: false, holidayHeld: undefined as boolean | undefined, openAct: undefined as Run["openAct"],
    crowdMax: 4, crowdLeft: 0, leftRank: undefined as number | null | undefined, haltSold: 0, panicBuy: false, lastHalt: -99,
    marks: new Set<string>(), lastBlip: 0, bid: 0, since: 0, scale: { lo: 0, hi: 0 },
    tap: null as null | { at: number; cash: number; shares: number; debt: number; n: number; firstMs: number | null },
  }).current;
  S.phase = phase;

  const priceAt = (h: number) => {
    const i = Math.floor(h);
    const f = h - i;
    return i >= N - 1 ? T.p[N - 1] : T.p[i] + (T.p[i + 1] - T.p[i]) * f;
  };
  const holding = () => S.shares > 0;
  const equity = (p: number) => S.cash + S.shares * p - S.debt;
  const say = (t: string, tone?: "up" | "down" | "dark", ms = 1200) => {
    setToast({ t, tone });
    setTimeout(() => setToast((x) => (x && x.t === t ? null : x)), ms);
  };
  const ms = () => Math.round(performance.now() - S.t0);

  function buy(why?: Trade["why"]) {
    if (holding() || S.cash <= 0.05) return;
    S.tap = why === undefined ? { at: performance.now(), cash: S.cash, shares: S.shares, debt: S.debt, n: S.trades.length, firstMs: S.firstMs } : null;
    const p = priceAt(S.head);
    const e = S.cash;
    const L = S.levSet;
    S.shares = (e * L) / p;
    S.debt = e * (L - 1);
    S.cash = 0;
    const i = Math.floor(S.head);
    S.trades.push({ k: "buy", i, day: T.day[i], p, ms: ms(), why });
    if (level.twist === "halt" && S.head > ev.halts[0] && S.head < (ev.halts[ev.halts.length - 1] ?? 0) + 6) S.panicBuy = true;
    if (why !== "start") {
      sfx.tap();
      buzz(18);
    }
    bump();
  }
  function sell(why?: Trade["why"]) {
    if (!holding()) return;
    const p = priceAt(S.head);
    if (S.locked && why !== "liq" && why !== "end") {
      S.pendingLock = true;
      S.lockTries += 1;
      sfx.lock();
      buzz([30, 30, 30]);
      say("跌停了 · 卖不出去", "dark", 1500);
      bump();
      return;
    }
    const e = equity(p);
    const i = Math.floor(S.head);
    const entry = [...S.trades].reverse().find((t) => t.k === "buy");
    S.cash = e;
    S.shares = 0;
    S.debt = 0;
    S.pendingLock = false;
    S.trades.push({ k: "sell", i, day: T.day[i], p, ms: ms(), why });
    if (level.twist === "circle" && S.leftRank === undefined) S.leftRank = S.head < ev.peakI ? -1 : S.crowdLeft;
    if (level.twist === "halt" && S.head - S.lastHalt <= 3) S.haltSold += 1;
    if (why !== "end") {
      const up = !entry || p >= entry.p;
      up ? sfx.coin() : sfx.loss();
      buzz(up ? [20, 30, 40] : 60);
    }
    bump();
  }
  function reconcile(why: Trade["why"]) {
    if (S.finger && !holding()) buy(why);
    else if (!S.finger && holding()) sell(why);
  }
  function relever(L: number) {
    S.levSet = L;
    S.levMax = Math.max(S.levMax, L);
    if (L > 1) S.levAt = priceAt(S.head) / T.p[0] - 1;
    if (holding()) {
      const p = priceAt(S.head);
      const e = equity(p);
      S.shares = (e * L) / p;
      S.debt = e * (L - 1);
      S.cash = 0;
    }
    L > 1 ? sfx.gain() : sfx.tap();
    buzz(L > 1 ? [20, 40, 20, 40] : 12);
  }

  /** needHold：手里有货时，按住才往下数；松手就停在 3，提示“按住才开盘” */
  function countdown(then: () => void, needHold = false) {
    S.phase = "count";
    setPhase("count");
    setCount(3);
    const wait = needHold && !S.finger;
    setWaitHold(wait);
    if (!wait) sfx.tick();
    let n = 3;
    const id = setInterval(() => {
      if (needHold && !S.finger) {
        n = 3;
        setCount(3);
        setWaitHold(true);
        return;
      }
      setWaitHold(false);
      n -= 1;
      if (n > 0) {
        setCount(n);
        sfx.tick();
      } else {
        clearInterval(id);
        then();
        S.phase = "run";
        setPhase("run");
      }
    }, 600);
  }
  function start() {
    if (S.phase !== "ready") return;
    sfx.bell();
    if (level.startIn) {
      const p = T.p[0];
      S.shares = cap / p;
      S.cash = 0;
    }
    countdown(() => {
      S.t0 = performance.now();
      if (level.startIn) {
        if (!S.finger) sell("start");
      } else if (S.finger) {
        buy("start");
        S.firstMs = 0;
      }
    }, level.startIn);
  }
  useEffect(() => {
    if (level.startIn) return;
    const t = setTimeout(start, 2600);
    return () => clearTimeout(t);
  }, []);
  function hold(t: number, p: Pause, after: () => void) {
    S.phase = "pause";
    setPhase("pause");
    setPause(p);
    setTimeout(() => {
      setPause(null);
      after();
      countdown(() => reconcile("resume"));
    }, t);
  }

  function entryP() {
    const b = [...S.trades].reverse().find((t) => t.k === "buy");
    return b ? b.p : level.startIn ? T.p[0] : null;
  }
  function judgePlan() {
    if (!S.planTriggered || S.planFollowed !== null) return;
    S.planFollowed = plan === "cut" ? S.trades.some((t) => t.k === "sell" && t.i >= S.planAt && t.i <= S.planAt + 4) : holding();
  }
  function onTick(k: number) {
    const s = level;
    const day = T.day[k];
    for (const f of foes) for (const t of f.trades) if (t.i === k) say(`${sp(f.id).cn}${t.k === "buy" ? "买进了" : "卖掉了"}`, "dark", 1100);
    if (plan !== "none") {
      const e0 = entryP();
      if (S.planAt < 0 && holding() && e0 && T.p[k] <= e0 * 0.95) {
        S.planAt = k;
        S.planTriggered = true;
        sfx.alarm();
        buzz([40, 30, 40]);
        say(plan === "cut" ? "跌了 5%：你说过要走" : "跌了 5%：你说过要加", "dark", 1800);
      } else if (S.planAt >= 0 && k >= S.planAt + 4) judgePlan();
    }
    if (k % 2 === 1 && k > 0) {
      const chg = T.p[k] / T.p[k - 2 >= 0 ? k - 2 : 0] - 1;
      if (chg <= -0.045) {
        sfx.thud();
        buzz(40);
        setShake((x) => x + 1);
        say(`大跌 ${(chg * 100).toFixed(1)}%`, "down");
      } else if (chg >= 0.045) {
        sfx.gain();
        say(`大涨 +${(chg * 100).toFixed(1)}%`, "up");
      }
    }
    if (s.twist === "leverage") {
      const wasLocked = S.locked;
      S.locked = ev.lockDays.has(day);
      if (S.locked && !wasLocked && k % 2 === 0) {
        sfx.alarm();
        say("千股跌停 · 今天卖不出去", "dark", 1600);
      }
      if (wasLocked && !S.locked && S.pendingLock) {
        S.pendingLock = false;
        if (!S.finger) sell("lock");
      }
    }
    if (s.twist === "circle") {
      if (k <= ev.peakI) {
        const f = (T.p[k] - T.p[0]) / Math.max(1, ev.peak - T.p[0]);
        S.crowdMax = Math.max(S.crowdMax, Math.min(12, 4 + Math.round(8 * Math.max(0, f))));
      } else {
        const gone = Math.min(S.crowdMax, Math.floor((1 - T.p[k] / ev.peak) / 0.022));
        if (gone > S.crowdLeft) {
          S.crowdLeft = gone;
          sfx.paper();
          if (gone === 1) say("有人松手了", "dark");
          else if (gone === S.crowdMax) say("圈里只剩你了", "dark", 1500);
        }
      }
    }
  }

  useEffect(() => {
    if (phase !== "run") return;
    let raf = 0;
    let last = performance.now();
    const loop = (now: number) => {
      const dt = Math.max(0, Math.min(0.05, (now - last) / 1000));
      last = now;
      const prev = S.head;
      const sp = ev.base * ev.slowAt[Math.min(N - 1, Math.floor(prev))];
      let next = Math.min(N - 1, prev + dt * sp);
      S.runT += dt;
      if (holding()) S.heldT += dt;
      for (let k = Math.floor(prev) + 1; k <= Math.floor(next); k++) {
        onTick(k);
        if (level.twist === "holiday" && k === ev.hol && !S.holidayDone) {
          S.head = k;
          setHead(k);
          S.holidayDone = true;
          S.holidayHeld = holding();
          const was = holding();
          hold(4600, { k: "holiday" }, () => {
            S.head = k + 1;
            setHead(k + 1);
            sfx.bell();
            buzz([30, 50, 30]);
            say(`开盘 ${((T.p[k + 1] / T.p[k] - 1) * 100).toFixed(1)}%`.replace(/开盘 (\d)/, "开盘 +$1"), "up", 1600);
            setTimeout(() => {
              S.openAct = S.finger ? (was ? "hold" : "buy") : was ? "sell" : "none";
            }, 1700);
          });
          return;
        }
        if (level.twist === "halt" && ev.halts.includes(k) && S.haltsDone < ev.halts.indexOf(k) + 1) {
          S.head = k;
          setHead(k);
          S.haltsDone = ev.halts.indexOf(k) + 1;
          S.lastHalt = k;
          sfx.alarm();
          buzz([60, 40, 60]);
          setShake((x) => x + 1);
          hold(2600, { k: "halt", n: S.haltsDone }, () => {});
          return;
        }
      }
      if (level.twist === "leverage" && !S.offered && priceAt(next) >= T.p[0] * (1 + (level.lev?.at ?? 0.4))) {
        S.offered = true;
        S.head = next;
        setHead(next);
        sfx.heart?.();
        S.phase = "pause";
        setPhase("pause");
        setPause({ k: "offer" });
        return;
      }
      S.head = next;
      const p = priceAt(next);
      const e = equity(p);
      S.peak = Math.max(S.peak, e);
      S.low = Math.min(S.low, e);
      if (level.lev && S.debt > 0 && e <= floor) {
        S.liq = true;
        sell("liq");
        S.levSet = 1;
        sfx.stamp();
        buzz([80, 40, 80]);
        setShake((x) => x + 1);
        hold(1800, { k: "liq" }, () => {});
        return;
      }
      if (holding() && Math.floor(next) - S.lastBlip >= 2) {
        S.lastBlip = Math.floor(next);
        const entry = [...S.trades].reverse().find((t) => t.k === "buy");
        blip(p / (entry?.p || T.p[0]));
      }
      const g = e / cap - 1;
      for (const [m, txt] of [[0.2, "赚了两成！"], [0.5, "赚了五成！"], [1, "翻倍了！"]] as [number, string][]) {
        if (g >= m && !S.marks.has(txt)) {
          S.marks.add(txt);
          sfx.gain();
          buzz([15, 30, 15]);
          say(txt, "up");
        }
      }
      S.since += dt;
      if (S.since > 0.85) {
        S.since = 0;
        const id = ++S.bid;
        setBullets((b) => [...b.slice(-4), { id, text: pick(moodPool(level, T.p, Math.floor(next), ev.peakI)), top: LANES[id % LANES.length] }]);
      }
      setHead(next);
      if (next >= N - 1) {
        judgePlan();
        if (holding()) sell("end");
        S.phase = "end";
        setPhase("end");
        finish();
        return;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [phase]);

  function finish() {
    const r: Run = {
      id: level.id, eq: S.cash, peak: S.peak, low: S.low, trades: S.trades,
      held: S.runT ? S.heldT / S.runT : 0, firstMs: S.firstMs, lev: S.levMax, levAt: S.levAt, liq: S.liq, lockTries: S.lockTries,
      holidayHeld: S.holidayHeld, openAct: S.openAct, leftRank: level.twist === "circle" ? (S.leftRank === undefined ? null : S.leftRank) : undefined,
      crowdLeft: level.twist === "circle" ? S.crowdLeft : undefined, haltSold: level.twist === "halt" ? S.haltSold : undefined, panicBuy: level.twist === "halt" ? S.panicBuy : undefined,
      cap, plan, planTriggered: S.planTriggered, planFollowed: S.planFollowed,
    };
    setTimeout(() => onDone(r), 900);
  }

  function down() {
    if (S.finger) return;
    S.finger = true;
    setFinger(true);
    if (S.phase === "ready") {
      start();
      return;
    }
    if (S.phase === "count") return;
    if (S.firstMs === null && S.phase === "run" && !level.startIn) S.firstMs = ms();
    if (S.phase === "run") buy();
  }
  function up() {
    if (!S.finger) return;
    S.finger = false;
    setFinger(false);
    if (S.phase !== "run") return;
    const t = S.tap;
    if (t && holding() && S.trades.length === t.n + 1 && performance.now() - t.at < 300) {
      S.cash = t.cash;
      S.shares = t.shares;
      S.debt = t.debt;
      S.firstMs = t.firstMs;
      S.trades.length = t.n;
      S.tap = null;
      buzz(40);
      say("要一直按着，才算拿着", "dark", 1500);
      bump();
      return;
    }
    sell();
  }

  const view = useMemo(() => {
    const hi0 = Math.ceil(head);
    const seen = T.p.slice(0, hi0 + 1);
    let lo = Math.min(...seen);
    let hi = Math.max(...seen);
    const pad = (hi - lo) * 0.14 || hi * 0.05;
    lo -= pad;
    hi += pad;
    const s = S.scale;
    s.lo = s.lo ? s.lo + (lo - s.lo) * 0.3 : lo;
    s.hi = s.hi ? s.hi + (hi - s.hi) * 0.3 : hi;
    const X = (i: number) => (i / (N - 1)) * W;
    const Y = (v: number) => H - ((v - s.lo) / (s.hi - s.lo)) * H;
    const pts: string[] = [];
    for (let k = 0; k <= Math.floor(head); k++) pts.push(`${pts.length ? "L" : "M"}${X(k).toFixed(1)},${Y(T.p[k]).toFixed(1)}`);
    pts.push(`L${X(head).toFixed(1)},${Y(priceAt(head)).toFixed(1)}`);
    return { X, Y, d: pts.join("") };
  }, [head, level.id]);

  const p = priceAt(head);
  const e = equity(p);
  const d = e - cap;
  const cls = d > 0.05 ? "up" : d < -0.05 ? "down" : "";
  const isIn = holding();
  const lastBuy = [...S.trades].reverse().find((t) => t.k === "buy");
  const liqLine = level.lev && S.debt > 0 && S.shares > 0 ? (S.debt + floor - S.cash) / S.shares : null;
  const planE = plan !== "none" && holding() && S.planAt < 0 ? entryP() : null;
  const stateChip = phase === "pause" && pause?.k === "holiday" ? "休市中" : phase === "pause" && pause?.k === "halt" ? "暂停交易" : S.locked && isIn ? "跌停 · 卖不出" : isIn || (phase === "ready" && level.startIn) ? (S.levSet > 1 && S.debt > 0 ? `持有 · ${S.levSet} 倍` : "持有") : "空仓";
  const btnLabel = phase === "ready" ? (level.startIn ? "按住\n拿着" : "按住\n买入") : phase === "count" ? (finger ? "拿着" : level.startIn || isIn ? "按住\n拿着" : "按住\n买入") : phase === "pause" && pause?.k === "holiday" ? (finger ? "拿着" : isIn ? "按住\n拿着" : "按住\n买进") : phase === "pause" ? (finger ? "拿着" : "…") : phase === "end" ? "收盘" : S.locked && isIn && !finger ? "跌停\n卖不出" : finger ? "拿着" : "按住\n买入";
  const gone = S.crowdLeft;
  const crowdNow = S.crowdMax - gone;

  return (
    <div className="arc-game">
      <div className="arc-acct">
        <div>
          <div className="tiny bold">总资产</div>
          <b className={"num " + cls}>{wan(e)}<small> 万</small></b>
        </div>
        <div className="arc-acct-r">
          <span className={"arc-chip" + (isIn ? " in" : "")}>{stateChip}</span>
          <b className={"num " + cls}>{d >= 0 ? "+" : "−"}{wan(Math.abs(d))} 万</b>
        </div>
      </div>

      {level.twist === "circle" && phase !== "ready" && (
        <div className="arc-ring">
          <span className="tiny bold">抱团的人 {crowdNow + (isIn ? 1 : 0)}</span>
          <div className="arc-ring-row">
            <AnimatePresence>
              {Array.from({ length: S.crowdMax }).map((_, i) => i >= gone && (
                <motion.i key={i} className="arc-p" style={{ background: ["#D4432A", "#C79A2E", "#4E8792", "#A3AE91", "#8C8A70", "#E07A5F"][i % 6] }}
                  initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ y: -26, opacity: 0, rotate: 30 }} transition={{ type: "spring", stiffness: 380, damping: 18 }} />
              ))}
              {isIn && <motion.i key="me" className="arc-p me" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ y: 26, opacity: 0 }}>你</motion.i>}
            </AnimatePresence>
          </div>
        </div>
      )}

      <motion.div className="arc-chart" key={shake} animate={shake ? { x: [0, -8, 8, -5, 5, 0] } : undefined}
        style={{ background: isIn ? (d >= 0 ? "radial-gradient(circle at 70% 20%, rgba(212,67,42,.16), transparent 65%), #FFFBF1" : "radial-gradient(circle at 70% 20%, rgba(60,122,78,.18), transparent 65%), #FFFBF1") : "#FFFBF1" }}>
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="none" style={{ display: "block", overflow: "visible" }}>
          {[...ev.lockDays].filter((dd) => dd * 2 <= head).map((dd) => (
            <rect key={dd} x={view.X(dd * 2) - 2} width={view.X(dd * 2 + 1) - view.X(dd * 2) + 4} y={0} height={H} fill="rgba(42,42,28,.10)" />
          ))}
          {ev.hol >= 0 && head > ev.hol && <rect x={view.X(ev.hol)} width={Math.max(3, view.X(ev.hol + 1) - view.X(ev.hol))} y={0} height={H} fill="rgba(199,154,46,.25)" />}
          {ev.halts.filter((k) => k <= head).map((k) => <text key={k} x={view.X(k)} y={12} fontSize={11} fontWeight={900} textAnchor="middle" fill="#D4432A">熔断</text>)}
          {isIn && lastBuy && <line x1={0} x2={W} y1={view.Y(lastBuy.p)} y2={view.Y(lastBuy.p)} stroke="#77745A" strokeDasharray="4 4" strokeWidth={1} />}
          {liqLine && liqLine > S.scale.lo && (
            <g>
              <line x1={0} x2={W} y1={view.Y(liqLine)} y2={view.Y(liqLine)} stroke="#D4432A" strokeDasharray="6 4" strokeWidth={1.6} />
              <text x={4} y={view.Y(liqLine) - 4} fontSize={10.5} fontWeight={900} fill="#D4432A">强平线</text>
            </g>
          )}
          {planE && planE * 0.95 > S.scale.lo && (
            <g>
              <line x1={0} x2={W} y1={view.Y(planE * 0.95)} y2={view.Y(planE * 0.95)} stroke="#2D5F6B" strokeDasharray="3 4" strokeWidth={1.6} />
              <text x={W - 4} y={view.Y(planE * 0.95) + 13} fontSize={10.5} fontWeight={900} textAnchor="end" fill="#2D5F6B">{plan === "cut" ? "说好跌 5% 就走" : "说好跌 5% 就加"}</text>
            </g>
          )}
          <path d={view.d} fill="none" stroke={isIn ? (d >= 0 ? "#D4432A" : "#3C7A4E") : "#2A2A1C"} strokeWidth={2.6} strokeLinejoin="round" />
          <defs><clipPath id="foe-clip" clipPathUnits="objectBoundingBox"><circle cx=".5" cy=".5" r=".5" /></clipPath></defs>
          {foes.map((f, fi) => f.trades.filter((t) => t.i <= head).map((t, j) => {
            const cx = view.X(t.i);
            const cy = view.Y(T.p[t.i]) + (fi ? 19 : -19);
            return (
              <g key={f.id + j}>
                <line x1={cx} x2={cx} y1={view.Y(T.p[t.i])} y2={cy} stroke="#77745A" strokeWidth={1} />
                <circle cx={cx} cy={cy} r={10.5} fill="#FBF4E4" stroke={t.k === "buy" ? "#D4432A" : "#2D5F6B"} strokeWidth={2.4} />
                <image href={ART(`species_${f.id}`)} x={cx - 9} y={cy - 9} width={18} height={18} clipPath="url(#foe-clip)" preserveAspectRatio="xMidYMin slice" />
              </g>
            );
          }))}
          {S.trades.filter((t) => t.why !== "end").map((t, i) => (
            <g key={i}>
              <circle cx={view.X(t.i)} cy={view.Y(t.p)} r={7.5} fill={t.why === "liq" ? "#2A2A1C" : t.k === "buy" ? "#D4432A" : "#2D5F6B"} stroke="#2A2A1C" strokeWidth={1.4} />
              <text x={view.X(t.i)} y={view.Y(t.p) + 3.5} fontSize={9} fontWeight={900} textAnchor="middle" fill="#fff">{t.why === "liq" ? "强" : t.k === "buy" ? "买" : "卖"}</text>
            </g>
          ))}
          <circle cx={view.X(head)} cy={view.Y(p)} r={5} fill={isIn ? "#F3D27F" : "#2A2A1C"} stroke="#2A2A1C" strokeWidth={1.5} />
        </svg>
        <div className="ride-bullets">
          <AnimatePresence>
            {bullets.map((b) => (
              <motion.span key={b.id} className="ride-bullet" style={{ top: `${b.top}%` }} initial={{ x: 380, opacity: 0 }} animate={{ x: -260, opacity: [0, 1, 1, 0] }} transition={{ duration: 4, ease: "linear" }}
                onAnimationComplete={() => setBullets((xs) => xs.filter((x) => x.id !== b.id))}>{b.text}</motion.span>
            ))}
          </AnimatePresence>
        </div>
        <AnimatePresence>
          {toast && (
            <motion.div key={toast.t} className={"arc-toast " + (toast.tone || "") + (toast.t.length > 6 ? " long" : "")} initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ opacity: 0, y: -18 }}>{toast.t}</motion.div>
          )}
        </AnimatePresence>
        <span className="arc-hidden tiny">日期已隐藏</span>
        <span className="crowd-tag" style={{ left: 8, bottom: 4 }}>弹幕为虚构的散户声音</span>

        <AnimatePresence>
          {phase === "ready" && (
            <motion.div key="ready" className="arc-over ready" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="arc-how">
                <motion.span className="arc-hand" animate={{ y: [0, 8, 0] }} transition={{ repeat: Infinity, duration: 1.2 }}>☝</motion.span>
                <div><b>手指按着 = 拿着</b><b>手指松开 = 卖掉</b></div>
              </div>
              <div className="arc-how-sub">不用点，按多久就拿多久</div>
              <div className="arc-rule">{level.rule}</div>
            </motion.div>
          )}
          {phase === "count" && (
            waitHold ? (
              <motion.div key="wait" className="arc-count wait" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <motion.span className="arc-hand" animate={{ y: [0, 10, 0] }} transition={{ repeat: Infinity, duration: 1 }}>☝</motion.span>
                <b>按住才开盘</b>
              </motion.div>
            ) : (
              <motion.div key={"c" + count} className="arc-count" initial={{ scale: 1.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ opacity: 0 }}>{count}</motion.div>
            )
          )}
          {pause?.k === "holiday" && <Holiday key="hol" holding={isIn} finger={finger} />}
          {pause?.k === "halt" && <Halt key="halt" n={pause.n} />}
          {pause?.k === "liq" && (
            <motion.div key="liq" className="arc-over dark" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <motion.b className="arc-stamp" initial={{ scale: 2.6, rotate: -20 }} animate={{ scale: 1, rotate: -8 }}>强制平仓</motion.b>
              <span className="mt8">亏到只剩 {wan(floor)} 万，借你钱的人替你卖了。</span>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {pause?.k === "offer" ? (
        <Offer noMax={noMax} floor={floor} onPick={(L) => {
          relever(L);
          setPause(null);
          countdown(() => reconcile("resume"), holding());
        }} />
      ) : (
        <div className="arc-pad">
          <button className={"arc-btn" + (finger ? " on" : "") + (phase === "ready" ? " ready" : "") + (phase === "pause" && pause?.k === "halt" ? " frozen" : "")}
            onPointerDown={(e) => { e.preventDefault(); e.currentTarget.setPointerCapture?.(e.pointerId); down(); }}
            onPointerUp={up} onPointerCancel={up} onLostPointerCapture={up} onContextMenu={(e) => e.preventDefault()}>
            {btnLabel}
          </button>
          <div className="arc-hint">
            {phase === "ready" ? (level.startIn ? "你手里有货 · 按住它，开盘" : "你现在空仓 · 马上开盘") : phase === "count" ? (waitHold ? "按住才开盘：按着 = 拿着" : level.startIn ? "一直按着，开盘后就是拿着" : finger ? "开盘时按着 = 买进去" : "想买就按住；不按 = 先不买") : phase === "pause" && pause?.k === "holiday" ? (isIn ? "按着过节 = 节后接着拿；松手 = 开盘卖" : "按着过节 = 节后开盘买进") : phase === "pause" ? "先别急" : finger ? <><b className="arc-hint-key">松手</b> = 卖掉</> : <><b className="arc-hint-key">按住</b> = 买入，一直按着 = 拿着</>}
          </div>
        </div>
      )}
    </div>
  );
}

function moodPool(l: Level, p: number[], k: number, peakI: number) {
  const P = l.pool;
  const back = p[Math.max(0, k - 8)];
  const hi = Math.max(...p.slice(0, k + 1));
  const lo = Math.min(...p.slice(0, k + 1));
  const r = p[k] / back - 1;
  let m: keyof Level["pool"] = "flat";
  if (p[k] / hi - 1 < -0.15) m = "fear";
  else if (k > peakI && p[k] / Math.min(...p.slice(peakI, k + 1)) - 1 > 0.06) m = "rebound";
  else if (p[k] >= hi * 0.985 && p[k] / lo > 1.15) m = "hot";
  else if (r > 0.03) m = "up";
  else if (r < -0.03) m = "down";
  return P[m] || P.flat || ["……"];
}

function Holiday({ holding, finger }: { holding: boolean; finger: boolean }) {
  const [d, setD] = useState(1);
  const [q, setQ] = useState(6);
  useEffect(() => {
    sfx.crowd();
    const a = setInterval(() => setD((x) => Math.min(7, x + 1)), 520);
    const b = setInterval(() => setQ((x) => Math.min(30, x + 1)), 150);
    return () => {
      clearInterval(a);
      clearInterval(b);
    };
  }, []);
  const plan = finger ? (holding ? "节后开盘：继续拿着" : "节后开盘：买进去") : holding ? "节后开盘：卖掉" : "节后开盘：不买";
  return (
    <motion.div className="arc-over holiday" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <div className="row gap12" style={{ alignItems: "center" }}>
        <motion.b key={d} className="arc-cal display" initial={{ rotateX: 90 }} animate={{ rotateX: 0 }}>休</motion.b>
        <div>
          <div className="display" style={{ fontSize: 24 }}>休市第 {d} 天</div>
          <div className="small">营业部门口排队开户的人：{q}</div>
        </div>
      </div>
      <div className="q-lane mt8">{Array.from({ length: Math.min(q, 22) }).map((_, i) => <i key={i} className="q-person" style={{ background: ["#D4432A", "#C79A2E", "#4E8792", "#A3AE91"][i % 4] }} />)}</div>
      <div className="arc-plan mt8">{plan}<span className="tiny">（按住 = 拿着 / 买进，松手 = 卖掉 / 不买）</span></div>
    </motion.div>
  );
}

function Halt({ n }: { n: number }) {
  return (
    <motion.div className="arc-over halt" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <motion.b className="arc-stamp red" initial={{ scale: 2.4, rotate: -16 }} animate={{ scale: 1, rotate: -6 }}>熔断</motion.b>
      <div className="display mt8" style={{ fontSize: 20 }}>第 {n} 次 · 暂停交易</div>
      <div className="arc-sand mt8"><i /></div>
      <div className="small mt4">谁都动不了。等它重新开盘。</div>
    </motion.div>
  );
}

function Offer({ onPick, noMax, floor }: { onPick: (L: number) => void; noMax?: boolean; floor: number }) {
  return (
    <motion.div className="arc-offer" initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
      <div className="row gap8" style={{ alignItems: "center" }}>
        <motion.span className="arc-phone" animate={{ rotate: [0, -14, 14, -10, 10, 0] }} transition={{ repeat: Infinity, duration: 1.1 }}>📞</motion.span>
        <div>
          <b className="display" style={{ fontSize: 21 }}>有人要借钱给你</b>
          <div className="small">借得越多，赚得越多，亏得也越多。</div>
        </div>
      </div>
      <div className="arc-offer-row mt12">
        <button className="btn" onClick={() => onPick(1)}>不借</button>
        <button className="btn" onClick={() => onPick(2)}><b>借 1 倍</b><span>涨跌 ×2</span></button>
        {noMax ? (
          <button className="btn" disabled><b>借 3 倍</b><span>冷静亭里说过不碰</span></button>
        ) : (
          <button className="btn primary" onClick={() => onPick(4)}><b>借 3 倍</b><span>涨跌 ×4</span></button>
        )}
      </div>
      <div className="tiny mt8 center">亏到只剩 {wan(floor)} 万，会被强制卖出。</div>
    </motion.div>
  );
}
