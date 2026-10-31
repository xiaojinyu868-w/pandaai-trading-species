import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Scene } from "../data";
import { lockedDay, pct, ps, sharesOf } from "../game/engine";
import { aiPick, sp } from "../game/meta";
import { cur, useGame } from "../game/store";
import { buzz, sfx } from "../lib/sound";
import { Fade, SpeciesAvatar } from "../ui/kit";
import { FFHeader, PlanPrompt, PosBar, useFinish } from "./common";

interface Lot { n: number; entry: number }
const md = (d: string) => `${Number(d.slice(5, 7))}/${Number(d.slice(8, 10))}`;

/* ---------------- 夏 · 2015：逐日格子 + 跌停锁 + 强制平仓 ---------------- */
export function FF2015({ scene }: { scene: Scene }) {
  const { g } = useGame();
  const rec = cur(g!);
  const finish = useFinish(scene);
  const path = scene.path!;
  const days = path.days;
  const t1 = path.t + 1;
  const e0 = path.ends[0];
  const e1 = path.ends[1];
  const s0 = sharesOf(scene, rec.option);
  const notes = useMemo(() => Object.fromEntries((scene.fast_forward.grid || []).filter((x) => x.note).map((x) => [x.date, x.note!])), [scene]);
  const [i, setI] = useState(t1 - 1);
  const [running, setRunning] = useState(false);
  const [lots, setLots] = useState<Lot[]>(s0 ? [{ n: s0, entry: days[t1].open }] : []);
  const [seg1, setSeg1] = useState(0);
  const [seg2, setSeg2] = useState(0);
  const [pending, setPending] = useState<number>(0);
  const [locked, setLocked] = useState(0);
  const [lockFlash, setLockFlash] = useState<number | null>(null);
  const [sellDay, setSellDay] = useState<string | undefined>();
  const [forced, setForced] = useState(false);
  const [planState, setPlanState] = useState<"idle" | "ask" | "done">(rec.plan && rec.plan !== "none" && (s0 > 0 || rec.plan === "add") ? "idle" : "done");
  const [planFollowed, setPlanFollowed] = useState<boolean | null>(null);
  const [actions, setActions] = useState<string[]>([]);
  const [finished, setFinished] = useState(false);
  const ref = useRef({ lots, seg1, seg2, pending });
  ref.current = { lots, seg1, seg2, pending };

  const shares = lots.reduce((a, l) => a + l.n, 0);
  const segOf = (k: number) => (k <= e0 ? 1 : 2);
  const unreal = (k: number, ls = lots) => ls.reduce((a, l) => a + l.n * ps(pct(l.entry, days[k].close)), 0);
  const dayPct = (k: number) => pct(days[k - 1].close, days[k].close);
  const isLocked = (k: number) => lockedDay(scene, k);
  const pnl = seg1 + seg2 + (i >= t1 ? unreal(i) : 0);

  function realize(k: number, n: number) {
    let left = n;
    let got = 0;
    const ls = ref.current.lots.map((l) => ({ ...l }));
    for (const l of ls) {
      const take = Math.min(l.n, left);
      got += take * ps(pct(l.entry, days[k].close));
      l.n -= take;
      left -= take;
    }
    const rest = ls.filter((l) => l.n > 0);
    if (segOf(k) === 1) setSeg1((v) => v + got);
    else setSeg2((v) => v + got);
    setLots(rest);
    return rest;
  }

  // 每天推进
  useEffect(() => {
    if (!running || finished) return;
    if (planState === "ask") return;
    const t = setTimeout(() => step(), 780);
    return () => clearTimeout(t);
  }, [running, i, planState, finished]);

  function step() {
    const k = i + 1;
    if (k > e1) return end();
    setI(k);
    const isLock = isLocked(k);
    sfx.tick();
    if (isLock) buzz(60);
    let ls = ref.current.lots;
    // 委托卖出
    if (ref.current.pending > 0) {
      if (isLock) {
        setLocked((v) => v + 1);
        setLockFlash(k);
        sfx.lock();
      } else {
        ls = realize(k, ref.current.pending);
        setPending(0);
        setSellDay(days[k].date);
        sfx.coin();
      }
    }
    // 强制平仓（只看 A）
    if (rec.option === "A" && ls.length && !forced) {
      const equity = g!.money + ref.current.seg1 + ref.current.seg2 + unreal(k, ls);
      if (equity < 5) {
        setForced(true);
        ls = realize(k, ls.reduce((a, l) => a + l.n, 0));
        setPending(0);
        setSellDay(days[k].date);
        sfx.alarm();
        setActions((a) => [...a, "forced"]);
      }
    }
    // 计划触发
    if (planState === "idle" && k <= e1) {
      const base = days[t1].open;
      if (pct(base, days[k].close) <= -5) {
        setPlanState("ask");
        setRunning(false);
      }
    }
    // 第一段结算：重新记成本
    if (k === e0 && ls.length) {
      const got = ls.reduce((a, l) => a + l.n * ps(pct(l.entry, days[k].close)), 0);
      setSeg1((v) => v + got);
      setLots(ls.map((l) => ({ ...l, entry: days[k].close })));
    }
  }

  function end() {
    let s2 = ref.current.seg2;
    const ls = ref.current.lots;
    if (ls.length) s2 += ls.reduce((a, l) => a + l.n * ps(pct(l.entry, days[e1].close)), 0);
    setSeg2(s2);
    setLots([]);
    setRunning(false);
    setFinished(true);
    const planTriggered = rec.plan !== "none" && !!rec.plan && planFollowed !== null;
    finish({
      seg1: ref.current.seg1, seg2: s2, extra: 0,
      ff: { actions, changes: actions.filter((a) => a !== "forced").length, planTriggered, planFollowed: planTriggered ? planFollowed : true, ruleFollowed: null, sellDay, locked, forced },
    });
  }

  function sell(n: number) {
    if (!shares || pending >= shares) return;
    sfx.tap();
    setPending(Math.min(shares, pending + n));
    setActions((a) => [...a, `sell${n}`]);
  }

  function followPlan(follow: boolean) {
    setPlanFollowed(follow);
    setPlanState("done");
    if (follow) {
      sfx.stamp();
      if (rec.plan === "cut" && isLocked(i)) {
        setPending(shares);
      } else if (rec.plan === "cut") {
        realize(i, shares);
        setSellDay(days[i].date);
      } else {
        setLots((ls) => [...ls, { n: 1, entry: days[i].close }]);
      }
      setActions((a) => [...a, `plan-${rec.plan}`]);
    }
    setRunning(true);
  }

  const grid = [];
  for (let k = t1; k <= e1; k++) grid.push(k);
  const curP = i >= t1 ? dayPct(i) : 0;
  const aiSellers = g!.opponents.filter((id) => aiPick(id, scene.id).ff === "sell" && sharesOf(scene, aiPick(id, scene.id).option) > 0);
  let aiSellDay = e0 + 1;
  while (aiSellDay < e1 && isLocked(aiSellDay)) aiSellDay++;
  const aiWait = aiSellDay - e0 - 1;

  return (
    <div>
      <FFHeader scene={scene} kicker="一天一天过。想卖就按“卖出”，但跌停的日子卖不掉。" />
      <div className="card mt12" style={{ background: "#2A2A1C", color: "#FBF4E4" }}>
        <div className="row between">
          <div>
            <div className="tiny" style={{ color: "#cfc6a8" }}>{i >= t1 ? `${days[i].date} · 第 ${i - path.t} 个交易日` : "决策日之后"}</div>
            <div className="display num" style={{ fontSize: 44 }}>{days[Math.max(i, path.t)].close.toFixed(0)}</div>
            <div className="tiny" style={{ color: "#cfc6a8" }}>{path.instrument}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div className="display num" style={{ fontSize: 34, color: curP >= 0 ? "#ff8a6b" : "#8fd19e" }}>{i >= t1 ? `${curP >= 0 ? "+" : "−"}${Math.abs(curP).toFixed(2)}%` : "—"}</div>
            {i >= t1 && isLocked(i) && <div className="pill" style={{ background: "#3C7A4E", color: "#fff" }}>🔒 卖不出去</div>}
            {i >= t1 && notes[days[i].date] && <div className="tiny mt4" style={{ color: "#F3D27F", maxWidth: 150 }}>{notes[days[i].date]}</div>}
          </div>
        </div>
      </div>
      <div className="mt12" style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 5 }}>
        {grid.map((k) => {
          const p = dayPct(k);
          const on = k <= i;
          const lk = isLocked(k);
          const strong = Math.min(1, Math.abs(p) / 7);
          return (
            <motion.div key={k} animate={on ? { scale: [0.7, 1.08, 1], opacity: 1 } : { opacity: 0.35 }} transition={{ duration: 0.35 }}
              className={lockFlash === k ? "shake" : ""}
              style={{ border: "2px solid #2A2A1C", borderRadius: 8, padding: "5px 2px", textAlign: "center", background: on ? (p >= 0 ? `rgba(212,67,42,${0.2 + strong * 0.8})` : `rgba(60,122,78,${0.2 + strong * 0.8})`) : "#FBF4E4", color: on && strong > 0.5 ? "#fff" : "#2A2A1C", position: "relative", outline: k === e0 ? "2px dashed #C79A2E" : "none", outlineOffset: 1 }}>
              <div style={{ fontSize: 9, fontWeight: 700, opacity: 0.85 }}>{md(days[k].date)}</div>
              <div style={{ fontSize: 12, fontWeight: 900 }}>{on ? `${p >= 0 ? "+" : ""}${p.toFixed(1)}` : "?"}</div>
              {on && lk && <span style={{ position: "absolute", right: -4, top: -8, fontSize: 13 }}>🔒</span>}
              {sellDay === days[k].date && <span style={{ position: "absolute", left: -4, top: -8, fontSize: 12 }}>💰</span>}
            </motion.div>
          );
        })}
      </div>
      <div className="tiny mt4">黄色虚线那天是第一段结算日（第 5 个交易日）。🔒 的日子卖不出去。{scene.fast_forward.online_note}</div>
      <div className="mt12"><PosBar shares={shares} pnl={pnl} /></div>
      {pending > 0 && <div className="pill warn mt8">卖出委托 {pending} 份 · {lockFlash === i ? "跌停排队中，未成交" : "收盘成交"}</div>}
      {forced && <div className="card mt8" style={{ background: "#FBE3DC" }}><b>强制平仓</b><div className="small">加了杠杆，资金跌到 5 万以下，券商替你卖掉了全部仓位（游戏化处理）。</div></div>}
      <AnimatePresence>{planState === "ask" && <div className="mt12"><PlanPrompt plan={rec.plan as "cut" | "add"} pctNow={pct(days[t1].open, days[i].close)} shares={shares} onFollow={() => followPlan(true)} onIgnore={() => followPlan(false)} /></div>}</AnimatePresence>
      {!finished ? (
        <div className="row gap8 mt12">
          {i < t1 || !running ? (
            <button className="btn season big grow" onClick={() => { sfx.bell(); setRunning(true); }}>{i < t1 ? "▶ 开盘" : "▶ 继续"}</button>
          ) : (
            <button className="btn grow" onClick={() => setRunning(false)}>❚❚ 暂停</button>
          )}
          <button className="btn" disabled={!shares || pending >= shares || i < t1} onClick={() => sell(1)}>卖 1 份</button>
          <button className="btn primary" disabled={!shares || pending >= shares || i < t1} onClick={() => sell(shares)}>全卖</button>
        </div>
      ) : (
        <Fade>
          <div className="card mt12" style={{ background: "#FFF6DE" }}>
            <div className="row between"><span>第一段（到 {md(days[e0].date)}）</span><b>{seg1}</b></div>
            <div className="row between mt4"><span>第二段（到 {md(days[e1].date)}）</span><b>{seg2}</b></div>
            <div className="small mt8">{sellDay ? `你在 ${md(sellDay)} 卖出。` : s0 ? "你一直拿着。" : "你早就离场了。"}{locked ? ` 有 ${locked} 次想卖却遇上跌停，没卖掉。` : ""}</div>
            {aiSellers.length > 0 && <div className="tiny mt4">{aiSellers.map((id) => sp(id).cn).join("、")}在第一段之后卖，{aiWait ? `前 ${aiWait} 天都卖不出去，${md(days[aiSellDay].date)} 才成交。` : `${md(days[aiSellDay].date)} 就成交了。`}</div>}
          </div>
        </Fade>
      )}
    </div>
  );
}

/* ---------------- 秋 B · 量化踩踏：出口板 ---------------- */
export function FFQuant({ scene }: { scene: Scene }) {
  const { g } = useGame();
  const rec = cur(g!);
  const finish = useFinish(scene);
  const card = scene.fast_forward.cards[0];
  const s0 = sharesOf(scene, rec.option);
  const [phase, setPhase] = useState<"crash" | "plan" | "exit" | "rebound" | "done">("crash");
  const [shown, setShown] = useState(0);
  const [planFollowed, setPlanFollowed] = useState<boolean | null>(null);
  const dip = card.dip;
  const planOn = !!rec.plan && rec.plan !== "none" && !!dip && (s0 > 0 || rec.plan === "add");
  const days = card.days || [];
  const actors = [{ id: "me", opt: rec.option! }, ...g!.opponents.map((id) => ({ id, opt: aiPick(id, scene.id).option }))];
  const crowdOf = (k: string) => actors.filter((a) => a.opt === k).length;
  const myExtra = rec.option === "C" || rec.option === "D" ? -(crowdOf(rec.option) - 1) : 0;
  const aiExtra = Object.fromEntries(g!.opponents.map((id) => {
    const o = aiPick(id, scene.id).option;
    return [id, o === "C" || o === "D" ? -(crowdOf(o) - 1) : 0];
  }));

  useEffect(() => {
    if (phase !== "crash") return;
    sfx.alarm();
    let v = 0;
    const target = days[0]?.pct ?? -7.5;
    const id = setInterval(() => {
      v = Math.max(target, v - 0.3);
      setShown(v);
      if (v <= target) {
        clearInterval(id);
        setTimeout(() => setPhase(planOn ? "plan" : "exit"), 900);
      }
    }, 40);
    return () => clearInterval(id);
  }, [phase]);

  function settle() {
    let seg1 = s0 * card.per_share;
    let s = s0;
    if (planOn && planFollowed && dip) {
      if (rec.plan === "cut") {
        seg1 = s0 * dip.per_share_at_trigger;
        s = 0;
      } else {
        seg1 = s0 * dip.per_share_at_trigger + (s0 + 1) * dip.rest_per_share;
        s = s0 + 1;
      }
    }
    const seg2 = s * scene.reveal.seg2.per_share;
    finish({
      seg1, seg2, extra: myExtra, aiExtra,
      ff: { actions: [], changes: 0, planTriggered: planOn, planFollowed: planOn ? planFollowed : true, ruleFollowed: rec.reason === "rule" ? rec.option === "B" : null },
    });
    setPhase("done");
  }

  const robots = 28;
  return (
    <div>
      <FFHeader scene={scene} kicker="所有人的规则，在同一天同时触发。" />
      <div className="card mt12" style={{ background: "#2A2A1C", color: "#FBF4E4", overflow: "hidden" }}>
        <div className="row between"><span className="tiny" style={{ color: "#cfc6a8" }}>{days[0]?.date} · 小市值指数</span><span className="pill" style={{ background: "#F3D27F" }}>出口板</span></div>
        <div className="display num" style={{ fontSize: 56, color: shown < 0 ? "#8fd19e" : "#ff8a6b" }}>{shown < 0 ? "−" : "+"}{Math.abs(shown).toFixed(1)}%</div>
        <div style={{ position: "relative", height: 96, marginTop: 6 }}>
          <div style={{ position: "absolute", right: 0, top: 18, width: 22, height: 60, background: "#F3D27F", border: "2px solid #FBF4E4", borderRadius: 4 }} />
          {Array.from({ length: robots }).map((_, k) => (
            <motion.span key={k} style={{ position: "absolute", top: 10 + (k % 4) * 20, width: 14, height: 16, borderRadius: 3, background: k % 7 === 0 ? "#D4432A" : "#9CC3C6", border: "1.5px solid #FBF4E4" }}
              initial={{ left: `${(k * 37) % 80}%` }} animate={phase === "crash" || phase === "plan" || phase === "exit" ? { left: "88%", top: 40 + (k % 3) * 6 } : { left: `${(k * 37) % 80}%` }}
              transition={{ duration: 1.2 + (k % 5) * 0.25, delay: (k % 6) * 0.08 }} />
          ))}
        </div>
        <div className="tiny" style={{ color: "#cfc6a8" }}>同一类规则在同一天发出卖出信号，大家都挤向同一扇窄门。</div>
      </div>
      <AnimatePresence>
        {phase === "plan" && dip && (
          <div className="mt12">
            <PlanPrompt plan={rec.plan as "cut" | "add"} pctNow={dip.pct_at_trigger} shares={s0}
              onFollow={() => { sfx.stamp(); setPlanFollowed(true); setPhase("exit"); }}
              onIgnore={() => { setPlanFollowed(false); setPhase("exit"); }} />
          </div>
        )}
      </AnimatePresence>
      {(phase === "exit" || phase === "rebound" || phase === "done") && (
        <Fade>
          <div className="card mt12">
            <b className="h3">亮牌后的出口板</b>
            <div className="col gap8 mt8">
              {(["C", "D"] as const).map((k) => {
                const who = actors.filter((a) => a.opt === k);
                return (
                  <div key={k} className="row between" style={{ background: "#FBF4E4", border: "2px solid #2A2A1C", borderRadius: 10, padding: "6px 10px" }}>
                    <span className="bold">{k} · {scene.options.find((o) => o.key === k)?.label}</span>
                    <span className="row gap4">
                      {who.map((a) => a.id === "me" ? <span key="me" className="pill" style={{ background: "#D4432A", color: "#fff" }}>你</span> : <SpeciesAvatar key={a.id} id={a.id} size={26} />)}
                      {who.length > 1 && <b className="down">每人 −{who.length - 1}</b>}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="tiny mt8">选了同一种卖出动作的人越多，出口越挤：同一动作每多 1 人，选它的每人多亏 1 万（游戏化处理）。</div>
          </div>
          {phase === "exit" && <button className="btn season block mt12" onClick={() => { sfx.gain(); setPhase("rebound"); }}>接下来四个交易日 →</button>}
        </Fade>
      )}
      {(phase === "rebound" || phase === "done") && (
        <Fade>
          <div className="row gap6 mt12">
            {days.map((d, k) => (
              <motion.div key={d.date} initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: k * 0.18 }} className="card" style={{ flex: 1, padding: "6px 2px", textAlign: "center", background: (d.pct ?? 0) >= 0 ? "#FBE3DC" : "#E3F0D9" }}>
                <div style={{ fontSize: 10, fontWeight: 700 }}>{md(d.date)}</div>
                <div className={(d.pct ?? 0) >= 0 ? "up bold" : "down bold"} style={{ fontSize: 13 }}>{(d.pct ?? 0) >= 0 ? "+" : ""}{d.pct?.toFixed(1)}</div>
              </motion.div>
            ))}
          </div>
          <div className="small mt8">{card.lines.slice(1).join(" ")}</div>
          {phase === "rebound" && <button className="btn primary block mt12" onClick={settle}>结算</button>}
          {phase === "done" && <div className="mt12"><PosBar shares={s0} pnl={cur(g!).money?.total ?? 0} label="这一场" /></div>}
        </Fade>
      )}
    </div>
  );
}
