import { animate, AnimatePresence, motion } from "framer-motion";
import { useEffect, useState, type ComponentType } from "react";
import type { OptKey, Scene } from "../data";
import { aiPick, sp } from "../game/meta";
import { cur, useGame } from "../game/store";
import { buzz, sfx } from "../lib/sound";
import { SpeciesAvatar } from "../ui/kit";

/**
 * 每个名场面自己的戏：开场、下单舞台、揭幕高光。
 * 只换呈现，不动桌游规则：选项、份数、快进动作和结算都照旧。没登记的场景用通用交易台。
 */

const PEOPLE = ["#D4432A", "#C79A2E", "#4E8792", "#A3AE91", "#8C8A70", "#E07A5F"];

function Person({ i, delay = 0 }: { i: number; delay?: number }) {
  return (
    <motion.span className="q-person" style={{ background: PEOPLE[i % PEOPLE.length] }}
      initial={{ x: 70, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay, type: "spring", stiffness: 320, damping: 24 }} />
  );
}

/* ---------- 春 · 924：排队 ---------- */

function Cold924({ onDone }: { scene: Scene; onDone: () => void }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    sfx.bell();
    sfx.crowd();
    const grow = setInterval(() => setN((x) => Math.min(x + 1, 26)), 120);
    const shut = setTimeout(() => {
      sfx.lock();
      buzz([20, 40, 20]);
    }, 2500);
    const t = setTimeout(onDone, 5200);
    return () => {
      clearInterval(grow);
      clearTimeout(shut);
      clearTimeout(t);
    };
  }, []);
  return (
    <motion.div className="cold cold-924" onClick={onDone} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="cold-kicker">长假前最后一个交易日 · 收盘后</div>
      <motion.div className="display cold-title" initial={{ y: 24, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
        营业部门口<br />排起了长队
      </motion.div>
      <div className="q-lane big mt16">
        {Array.from({ length: n }).map((_, i) => <Person key={i} i={i} />)}
      </div>
      <motion.div className="cold-cal" initial={{ rotateX: 90, opacity: 0 }} animate={{ rotateX: 0, opacity: 1 }} transition={{ delay: 2.4, duration: 0.5 }}>
        <b className="display">休</b>
        <span>明天起<br />休市 7 天</span>
      </motion.div>
      <div className="cold-skip">点一下继续</div>
      <motion.div className="cold-bar" initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ duration: 5.2, ease: "linear" }} />
    </motion.div>
  );
}

/** 924 的下单舞台：选 A、B 就是站进队尾，看得见前面排了多少人 */
function Queue924({ scene, joined }: { scene: Scene; joined: boolean | null }) {
  const { g } = useGame();
  const ai = g!.opponents.filter((id) => ["A", "B"].includes(aiPick(id, scene.id).option));
  const crowd = 9;
  const ahead = crowd + ai.length;
  useEffect(() => {
    if (joined) {
      sfx.hop();
      buzz(20);
    }
  }, [joined]);
  return (
    <div className="card q-stage">
      <div className="row between">
        <b>营业部门口</b>
        <motion.span key={String(joined)} className="pill" style={{ background: joined ? "var(--kite)" : "#F3D27F", color: joined ? "#fff8ec" : undefined }} initial={{ scale: 1.3 }} animate={{ scale: 1 }}>
          {joined ? `你排在第 ${ahead + 1} 位` : `已经排了 ${ahead} 人`}
        </motion.span>
      </div>
      <div className="q-lane mt8">
        {Array.from({ length: crowd }).map((_, i) => <Person key={i} i={i} delay={i * 0.05} />)}
        {ai.map((id) => <SpeciesAvatar key={id} id={id} size={28} />)}
        <AnimatePresence mode="popLayout">
          {joined ? (
            <motion.span key="me" className="q-me" initial={{ x: 60, scale: 0.4, opacity: 0 }} animate={{ x: 0, scale: 1, opacity: 1 }} exit={{ y: 24, opacity: 0 }} transition={{ type: "spring", stiffness: 420, damping: 20 }}>你</motion.span>
          ) : joined === false ? (
            <motion.span key="out" className="q-me out" initial={{ y: -16, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ opacity: 0 }}>你</motion.span>
          ) : (
            <motion.span key="slot" className="q-slot" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>?</motion.span>
          )}
        </AnimatePresence>
      </div>
      <div className="tiny mt8" style={{ color: "#cfc6a8" }}>
        {ai.length ? `${ai.map((id) => sp(id).cn).join("、")}已经排进去了。` : "两位 AI 对手都没排队。"}
        {joined ? "节后开盘铃一响，按开盘价买进。" : joined === false ? "你站在门外。" : "选 A 或 B，就是排进去。"}
      </div>
    </div>
  );
}

function Moment924() {
  const { g } = useGame();
  const rec = cur(g!);
  const joined = rec.option === "A" || rec.option === "B";
  const pos = (rec.queueSeen ?? 0) + 1;
  const [v, setV] = useState(0);
  useEffect(() => {
    const c = animate(0, 3.45, { duration: 1.8, delay: 0.3, ease: "easeOut", onUpdate: setV, onComplete: () => sfx.coin() });
    return () => c.stop();
  }, []);
  return (
    <div className="card moment">
      <div className="kicker" style={{ color: "#F3D27F" }}>节后第一天 · 10 月 8 日</div>
      <div className="row gap6 mt4" style={{ alignItems: "baseline" }}>
        <span className="display num" style={{ fontSize: 58, lineHeight: 1, color: "#ff8a6b" }}>{v.toFixed(2)}</span>
        <b style={{ fontSize: 22 }}>万亿</b>
      </div>
      <div className="small mt4">全天成交，历史纪录；开盘约 20 分钟就破了万亿（公开报道）。</div>
      <div className="moment-me mt8">
        {joined ? `你排在第 ${pos} 位，在高开 10.1% 的开盘价买进。` : rec.option === "C" ? "你没排队，在门外等回调。" : "你没排队，在门外看完了这一场。"}
      </div>
    </div>
  );
}

/* ---------- 登记 ---------- */

export interface Stage {
  Cold?: ComponentType<{ scene: Scene; onDone: () => void }>;
  Order?: ComponentType<{ scene: Scene; joined: boolean | null }>;
  /** 选项牌上的一个动词，让选择落到这一场的道具上 */
  tag?: Partial<Record<OptKey, string>>;
  /** 下单按钮上的字 */
  verb?: (opt: OptKey) => string;
  /** 下单后的印章 */
  stamp?: (opt: OptKey) => string;
  Moment?: ComponentType;
}

export const STAGES: Record<string, Stage> = {
  s924: {
    Cold: Cold924,
    Order: Queue924,
    tag: { A: "排进去", B: "排进去", C: "先不排", D: "不排" },
    verb: (o) => ({ A: "排进队伍 · 节后开盘买 2 份", B: "排进队伍 · 节后开盘买 1 份", C: "先不排 · 等回调", D: "不排了" })[o],
    stamp: (o) => (o === "A" || o === "B" ? "已排队" : "确认"),
    Moment: Moment924,
  },
};
