import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import type { Scene } from "../data";
import { money, sharesOf } from "../game/engine";
import { aiPick, sp } from "../game/meta";
import { cur, useGame } from "../game/store";
import { buzz, sfx } from "../lib/sound";
import { Fade, sleep, SpeciesAvatar } from "../ui/kit";
import { Big, FFHeader, PlanPrompt, PosBar, useFinish } from "./common";
import { FF2015, FFQuant } from "./FFDays";
import { FFBreaker, FFMoutai } from "./FFCrowd";

const HOW: Record<string, string> = {
  s924: "长假七天，看着开户的队伍越排越长；开盘铃一响，决定拿着、卖掉还是加仓。",
  s2015: "日子一天天往前走。想卖就按“卖出”，但跌停的日子卖不掉。",
  smt: "节后一周，盯着信号灯和人群。最后一起决定：留下，还是离开。",
  scb: "三次熔断，每次之后有 12 秒冷静期，然后可以调一档仓位。",
  squant: "所有人的规则在同一天触发，出口只有一个。",
  soil: "合约到期前一天。看看价格会去哪里。",
};

function MiniIntro({ scene, onDone }: { scene: Scene; onDone: () => void }) {
  useEffect(() => {
    sfx.bell();
    const t = setTimeout(onDone, 2600);
    return () => clearTimeout(t);
  }, []);
  return (
    <motion.div className="mini-intro" onClick={onDone} initial={{ opacity: 0, scale: 0.9, rotate: -2 }} animate={{ opacity: 1, scale: 1, rotate: 0 }} transition={{ type: "spring", stiffness: 260, damping: 18 }}>
      <div className="kicker" style={{ color: "#F3D27F" }}>这一场的小游戏</div>
      <motion.div className="display mt8" style={{ fontSize: 44, lineHeight: 1.05, textShadow: "3px 3px 0 #2A2A1C" }} initial={{ y: 24, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.15 }}>{scene.fast_forward.mechanic_name}</motion.div>
      <div className="h3 mt12">{scene.fast_forward.title}</div>
      <p className="body mt8" style={{ opacity: 0.92 }}>{HOW[scene.id]}</p>
      <div className="tiny mt12" style={{ color: "#fff8ec", opacity: 0.75 }}>点一下直接开始</div>
      <motion.div className="bar" initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ duration: 2.6, ease: "linear" }} />
    </motion.div>
  );
}

export function FFStep({ scene, onNext }: { scene: Scene; onNext: () => void }) {
  const { g } = useGame();
  const rec = cur(g!);
  const done = !!rec.money;
  const [intro, setIntro] = useState(!done);
  if (intro) return <div className="pad" style={{ paddingTop: 12 }}><MiniIntro scene={scene} onDone={() => setIntro(false)} /></div>;
  return (
    <div className="pad" style={{ paddingTop: 12 }}>
      {scene.id === "s924" && <FF924 scene={scene} />}
      {scene.id === "s2015" && <FF2015 scene={scene} />}
      {scene.id === "smt" && <FFMoutai scene={scene} />}
      {scene.id === "scb" && <FFBreaker scene={scene} />}
      {scene.id === "squant" && <FFQuant scene={scene} />}
      {scene.id === "soil" && <FFOil scene={scene} />}
      {done && (
        <Fade delay={0.2}>
          <button className="btn season big block mt16" onClick={() => { sfx.reveal(); onNext(); }}>揭幕：这到底是哪一次？</button>
        </Fade>
      )}
    </div>
  );
}

/* ---------------- 春 · 924：排队条 + 假期走马灯 + 开盘钟 ---------------- */
function FF924({ scene }: { scene: Scene }) {
  const { g } = useGame();
  const rec = cur(g!);
  const finish = useFinish(scene);
  const ff = scene.fast_forward;
  const card = ff.cards[0];
  const s0 = sharesOf(scene, rec.option);
  const [phase, setPhase] = useState<"holiday" | "bell" | "day1" | "plan" | "day2" | "decide" | "done">("holiday");
  const [day, setDay] = useState(0);
  const [shares, setShares] = useState(s0);
  const [realized, setRealized] = useState(0);
  const [planRes, setPlanRes] = useState<{ triggered: boolean; followed: boolean | null }>({ triggered: false, followed: null });
  const [shown, setShown] = useState(0);
  const ticker = ff.holiday_ticker || [];
  const d1 = card.days?.[0];
  const d2 = card.days?.[1];
  const dip = card.dip;
  const planOn = rec.plan && rec.plan !== "none" && dip && (s0 > 0 || rec.plan === "add");
  const queueAi = g!.opponents.filter((id) => ["A", "B"].includes(aiPick(id, scene.id).option));

  useEffect(() => {
    if (phase !== "holiday") return;
    if (day >= 7) {
      setPhase("bell");
      return;
    }
    const t = setTimeout(() => { sfx.paper(); setDay((d) => d + 1); }, day === 0 ? 400 : 900);
    return () => clearTimeout(t);
  }, [phase, day]);

  useEffect(() => {
    if (phase === "bell") {
      sfx.bell();
      buzz([80, 60, 80]);
      let v = 0;
      const target = d1?.open_pct ?? 10;
      const id = setInterval(() => {
        v = Math.min(target, v + target / 22);
        setShown(v);
        if (v >= target) {
          clearInterval(id);
          setTimeout(() => setPhase("day1"), 1300);
        }
      }, 45);
      return () => clearInterval(id);
    }
    if (phase === "day1") {
      let v = d1?.open_pct ?? 10;
      const target = d1?.close_pct ?? 4.6;
      const id = setInterval(() => {
        v = Math.max(target, v - 0.25);
        setShown(v);
        if (v <= target) {
          clearInterval(id);
          setTimeout(() => setPhase(planOn ? "plan" : "day2"), 1100);
        }
      }, 45);
      return () => clearInterval(id);
    }
    if (phase === "day2") {
      sfx.loss();
      setShown(d2?.close_pct ?? -6.6);
    }
  }, [phase]);

  const holidayLine = (n: number) => {
    const hit = ticker.find((t) => t.startsWith(`假期第 ${n} 天`));
    return hit ? hit.replace(/^假期第 \d+ 天：/, "") : ["市场休市，手机里的讨论没有休息。", "开户的人越来越多。", "亲戚饭桌上也在聊股票。", "券商连夜扩容开户系统。"][n % 4];
  };

  function settleSeg1(followed: boolean | null) {
    let r = 0;
    let s = s0;
    if (planOn && followed && dip) {
      if (rec.plan === "cut") {
        r = s0 * dip.per_share_at_trigger;
        s = 0;
      } else {
        r = s0 * dip.per_share_at_trigger + (s0 + 1) * dip.rest_per_share;
        s = s0 + 1;
      }
    } else {
      r = s0 * card.per_share;
    }
    setRealized(r);
    setShares(s);
  }

  function decide(action: "hold" | "sell" | "add" | "enter") {
    let s = shares;
    if (action === "sell") s = 0;
    if (action === "add" || action === "enter") s = s + 1;
    const seg2 = s * scene.reveal.seg2.per_share;
    finish({
      seg1: realized, seg2, extra: 0,
      ff: { actions: [action], changes: action === "hold" ? 0 : 1, planTriggered: planRes.triggered, planFollowed: planRes.triggered ? planRes.followed : true, ruleFollowed: null },
    });
    setShares(s);
    setPhase("done");
    sfx.stamp();
  }

  const pctColor = shown >= 0 ? "#D4432A" : "#3C7A4E";
  return (
    <div>
      <FFHeader scene={scene} kicker={s0 > 0 ? "放假七天不开门，节后第一天按开盘价买入。" : rec.option === "C" ? "你在等回调：跌下来了可以进 1 份。" : "你没参与，看看节后发生了什么。"} />
      <AnimatePresence mode="wait">
        {phase === "holiday" && (
          <motion.div key="hol" exit={{ opacity: 0 }} className="mt16">
            <div className="card center" style={{ background: "#FBF4E4", padding: 0, overflow: "hidden" }}>
              <div style={{ background: "#D4432A", color: "#fff", padding: "6px 0", fontWeight: 800, borderBottom: "2px solid #2A2A1C" }}>国庆长假 · 休市</div>
              <AnimatePresence mode="wait">
                <motion.div key={day} initial={{ rotateX: -90, opacity: 0 }} animate={{ rotateX: 0, opacity: 1 }} exit={{ rotateX: 90, opacity: 0 }} transition={{ duration: 0.35 }} style={{ padding: "16px 12px 18px", transformPerspective: 600 }}>
                  <div className="display" style={{ fontSize: 76, lineHeight: 1 }}>10/{Math.max(1, day)}</div>
                  <div className="small bold mt8">假期第 {Math.max(1, day)} 天</div>
                  <div className="body mt4">{holidayLine(Math.max(1, day))}</div>
                </motion.div>
              </AnimatePresence>
            </div>
            <div className="card mt12" style={{ background: "#2A2A1C", color: "#FBF4E4", padding: 12 }}>
              <div className="row between"><b>开户排队条</b><span className="tiny" style={{ color: "#cfc6a8" }}>排队的人越来越多</span></div>
              <div className="row mt8" style={{ gap: 3, flexWrap: "wrap" }}>
                {Array.from({ length: 6 + day * 4 }).map((_, i) => (
                  <motion.span key={i} initial={{ scale: 0 }} animate={{ scale: 1 }} style={{ width: 14, height: 20, borderRadius: "7px 7px 3px 3px", background: ["#D4432A", "#C79A2E", "#4E8792", "#A3AE91"][i % 4], border: "1.5px solid #FBF4E4" }} />
                ))}
                {queueAi.map((id) => <SpeciesAvatar key={id} id={id} size={24} />)}
                {s0 > 0 && <span className="pill" style={{ background: "#D4432A", color: "#fff" }}>你</span>}
              </div>
            </div>
            <button className="btn ghost sm block mt12" onClick={() => setDay(7)}>跳过假期</button>
          </motion.div>
        )}
        {(phase === "bell" || phase === "day1" || phase === "plan" || phase === "day2") && (
          <motion.div key="mkt" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="mt16">
            <motion.div className={"card center" + (phase === "bell" ? " shake" : "")} style={{ background: phase === "day2" ? "#E3F0D9" : "#FBE3DC", padding: "18px 12px" }}>
              <div className="kicker">{phase === "day2" ? `${d2?.date.slice(5).replace("-", " 月 ")} 日 · 节后第二天` : `${d1?.date.slice(5).replace("-", " 月 ")} 日 · 节后第一天`}</div>
              {phase === "bell" && <motion.div className="display" style={{ fontSize: 30 }} animate={{ scale: [1, 1.15, 1] }} transition={{ repeat: 3, duration: 0.4 }}>🔔 开盘！</motion.div>}
              <div className="mt8"><Big color={pctColor}>{shown >= 0 ? "+" : "−"}{Math.abs(shown).toFixed(1)}%</Big></div>
              <div className="small mt8">{phase === "bell" ? "高开" : phase === "day2" ? "第二天收盘" : "冲高回落，第一天收盘"}</div>
              {phase === "bell" && <div className="tiny mt4">开盘约 20 分钟，两市成交额就破了万亿（公开报道）</div>}
            </motion.div>
            {phase === "plan" && dip && (
              <div className="mt12">
                <PlanPrompt plan={rec.plan as "cut" | "add"} pctNow={dip.pct_at_trigger} shares={s0}
                  note={`你是按节后第一天的开盘价买的（当天高开 ${(d1?.open_pct ?? 0).toFixed(1)}%），收盘只剩 +${(d1?.close_pct ?? 0).toFixed(1)}%。`}
                  onFollow={() => { sfx.stamp(); setPlanRes({ triggered: true, followed: true }); settleSeg1(true); setPhase("day2"); }}
                  onIgnore={() => { sfx.tap(); setPlanRes({ triggered: true, followed: false }); settleSeg1(false); setPhase("day2"); }} />
              </div>
            )}
            {phase === "day2" && (
              <Fade delay={0.3}>
                <div className="card mt12">
                  <div className="small">{card.lines[2]}</div>
                  <div className="row between mt8"><span className="bold">每份仓位</span><b className="down">{card.per_share}</b></div>
                </div>
                <button className="btn season block mt12" onClick={() => { if (!planOn || !planRes.triggered) settleSeg1(null); setPhase("decide"); }}>结算这一段</button>
              </Fade>
            )}
          </motion.div>
        )}
        {(phase === "decide" || phase === "done") && (
          <motion.div key="dec" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt16 col gap12">
            <PosBar shares={shares} pnl={phase === "done" ? realized + shares * scene.reveal.seg2.per_share : realized} />
            {phase === "decide" ? (
              <div className="card">
                <b className="h3">{card.then}</b>
                <div className="col gap8 mt12">
                  {shares > 0 ? (
                    <>
                      <button className="btn block" onClick={() => decide("hold")}>拿着不动</button>
                      <button className="btn block" onClick={() => decide("sell")}>全部卖出</button>
                      <button className="btn block" onClick={() => decide("add")}>再加 1 份</button>
                    </>
                  ) : rec.option === "C" ? (
                    <>
                      <button className="btn block primary" onClick={() => decide("enter")}>回调了，进 1 份</button>
                      <button className="btn block" onClick={() => decide("hold")}>继续等</button>
                    </>
                  ) : (
                    <button className="btn block" onClick={() => decide("hold")}>继续不参与</button>
                  )}
                </div>
              </div>
            ) : (
              <div className="card center" style={{ background: "#FFF6DE" }}>
                <div className="small">第二天收盘之后，到第 20 个交易日，指数 {scene.reveal.seg2.pct > 0 ? "+" : ""}{scene.reveal.seg2.pct}%。{shares > 0 ? `你拿着 ${shares} 份，这一段 ${money(shares * scene.reveal.seg2.per_share)} 万。` : "你手里没有仓位，这一段不影响你。"}</div>
                <div className="tiny mt4">接下来去揭幕，看完整的账。</div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ---------------- 冬 B · 原油宝：负债牌 ---------------- */
function FFOil({ scene }: { scene: Scene }) {
  const { g } = useGame();
  const rec = cur(g!);
  const finish = useFinish(scene);
  const card = scene.fast_forward.cards[0];
  const s0 = sharesOf(scene, rec.option);
  const near = rec.option === "A";
  const far = rec.option === "B";
  const [price, setPrice] = useState(18.27);
  const [phase, setPhase] = useState<"drop" | "hit" | "debt" | "done">("drop");
  const loss = near ? s0 * card.per_share : far ? s0 * (card.far?.per_share ?? -4) : 0;
  const after = g!.money + loss;
  useEffect(() => {
    let v = 18.27;
    let step = 0.18;
    const id = setInterval(() => {
      step *= 1.045;
      v = Math.max(-37.63, v - step);
      setPrice(v);
      if (v < 0.4 && v > -0.6) buzz(30);
      if (v <= -37.63) {
        clearInterval(id);
        sfx.alarm();
        setTimeout(() => setPhase("hit"), 900);
      }
    }, 50);
    return () => clearInterval(id);
  }, []);
  const h = 220;
  const y = (p: number) => ((25 - p) / 65) * h;
  return (
    <div>
      <FFHeader scene={scene} kicker="4 月 20 日，5 月原油合约最后交易日的前一天" />
      <div className="card mt16 row gap12" style={{ alignItems: "stretch" }}>
        <div style={{ position: "relative", width: 70, height: h, background: "#FBF4E4", border: "2px solid #2A2A1C", borderRadius: 10, overflow: "hidden", flex: "none" }}>
          <div style={{ position: "absolute", left: 0, right: 0, top: y(0), height: 2, background: "#2A2A1C" }} />
          <div style={{ position: "absolute", left: 4, top: y(0) - 14, fontSize: 10, fontWeight: 800 }}>0 美元</div>
          <motion.div style={{ position: "absolute", left: 18, right: 18, background: price >= 0 ? "#2A2A1C" : "#3C7A4E", borderRadius: price >= 0 ? "6px 6px 0 0" : "0 0 6px 6px" }}
            animate={{ top: Math.min(y(price), y(0)), height: Math.max(2, Math.abs(y(price) - y(0))) }} transition={{ duration: 0.05 }} />
        </div>
        <div className="col grow" style={{ justifyContent: "center" }}>
          <div className="tiny">WTI 5 月合约</div>
          <Big color={price >= 0 ? "#2A2A1C" : "#3C7A4E"}>{price < 0 ? "−" : ""}{Math.abs(price).toFixed(2)}</Big>
          <div className="small">美元 / 桶</div>
          {price < 0 && <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="small bold mt8 down">历史上第一次跌到负数：手里有油的人，要倒贴钱请别人拿走。</motion.div>}
          <button className="btn sm mt12" disabled style={{ alignSelf: "flex-start" }}>🔒 卖出：产品已停止交易</button>
        </div>
      </div>
      <div className="tiny mt8">起点 18.27 美元（4 月 17 日结算价），终点 −37.63 美元（4 月 20 日结算价），都是公开报道的数字；中间的下跌过程是示意。</div>
      <AnimatePresence>
        {phase !== "drop" && (
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} className="col gap12 mt16">
            {near ? (
              <div className="card" style={{ background: "#E3F0D9" }}>
                <b className="h3">近月产品：本金亏光，还倒欠</b>
                <p className="body mt4">银行按 −37.63 美元给没移仓的人统一结算（公开报道）。游戏里每份亏 {Math.abs(card.per_share)} 万，你 {s0} 份：<b className="down">{loss} 万</b>。</p>
                <div className="row between mt8"><span>资金</span><b className="display num" style={{ fontSize: 34 }}>{g!.money} 万 → <span className={after < 0 ? "down" : ""}>{after} 万</span></b></div>
              </div>
            ) : far ? (
              <div className="card">
                <b className="h3">远月合约：躲开了最危险的那一天</b>
                <p className="body mt4">6 月合约同一天约 20.43 美元，{card.far?.pct}%（公开报道）。你 {s0} 份：<b className="down">{loss}</b>。</p>
              </div>
            ) : (
              <div className="card" style={{ background: "#FFF6DE" }}>
                <b className="h3">你没碰</b>
                <p className="body mt4">{rec.option === "C" ? "看不懂的东西不碰——这一次，这就是最好的决定。" : "观望的人，这一天什么都没发生。"}</p>
              </div>
            )}
            {near && after < 0 && phase === "hit" && (
              <motion.div initial={{ rotate: -8, scale: 0.6, opacity: 0 }} animate={{ rotate: -2, scale: 1, opacity: 1 }} className="card" style={{ background: "#2A2A1C", color: "#FBF4E4", position: "relative" }}>
                <div className="kicker" style={{ color: "#F3D27F" }}>负债牌</div>
                <div className="h2 mt4">你倒欠 {Math.abs(after)} 万</div>
                <div className="small mt4" style={{ opacity: 0.85 }}>资金低于 0 叫穿仓。终局时收益名次分记 0 分。</div>
                <div className="stamp" style={{ right: 12, top: 14, color: "#ff8a6b", borderColor: "#ff8a6b", mixBlendMode: "normal" }}>穿仓</div>
              </motion.div>
            )}
            {phase === "hit" && (
              <button className="btn primary block" onClick={() => {
                sfx.stamp();
                finish({ seg1: loss, seg2: 0, extra: 0, ff: { actions: [], changes: 0, planTriggered: false, planFollowed: true, ruleFollowed: null, debt: near && after < 0 } });
                setPhase("done");
              }}>{near && after < 0 ? "签收负债牌" : "记下这一笔"}</button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
