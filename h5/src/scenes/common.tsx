import { motion } from "framer-motion";
import { useEffect, useRef, type ReactNode } from "react";
import type { Scene } from "../data";
import { aiResult } from "../game/engine";
import { cur, useGame, type SeasonRec } from "../game/store";

export interface FFOut {
  seg1: number;
  seg2: number;
  extra: number;
  ff: NonNullable<SeasonRec["ff"]>;
  aiExtra?: Record<string, number>;
  note?: string;
}

export function useFinish(scene: Scene) {
  const { g, update } = useGame();
  return (o: FFOut) => {
    update((x) => {
      const r = cur(x);
      const ai: Record<string, any> = {};
      x.opponents.forEach((id) => (ai[id] = aiResult(scene, id, o.aiExtra?.[id] || 0)));
      const total = o.seg1 + o.seg2 + o.extra;
      let counted = total;
      if (r.recognized) {
        const vals = Object.values(ai).map((a: any) => a.total);
        counted = Math.round(vals.reduce((a: number, b: number) => a + b, 0) / Math.max(1, vals.length));
      }
      r.ff = o.ff;
      r.money = { seg1: o.seg1, seg2: o.seg2, extra: o.extra, total, counted, note: o.note };
      r.ai = ai;
    });
  };
}

export function FFHeader({ scene, kicker }: { scene: Scene; kicker?: string }) {
  return (
    <div>
      <div className="row between">
        <div className="kicker">快进 · 小游戏</div>
        <span className="pill season">{scene.fast_forward.mechanic_name}</span>
      </div>
      <div className="h2 mt4">{scene.fast_forward.title}</div>
      {kicker && <div className="small muted mt4">{kicker}</div>}
    </div>
  );
}

export function Big({ children, color }: { children: ReactNode; color?: string }) {
  return <div className="display num" style={{ fontSize: 64, lineHeight: 1, color, textShadow: "3px 3px 0 rgba(42,42,28,.9)" }}>{children}</div>;
}

/** 快进时的账户：总资产、这一场盈亏、持仓，数字一变就闪一下 */
export function PosBar({ shares, pnl, label = "持仓" }: { shares: number; pnl: number; label?: string }) {
  const { g } = useGame();
  const total = (g?.money ?? 20) + pnl;
  const prev = useRef(pnl);
  const dir = pnl > prev.current ? 1 : pnl < prev.current ? -1 : 0;
  useEffect(() => void (prev.current = pnl), [pnl]);
  const cls = pnl > 0 ? "up" : pnl < 0 ? "down" : "";
  return (
    <motion.div key={pnl} className="card acct" initial={dir ? { backgroundColor: dir > 0 ? "#FBD9CF" : "#D6EBD9" } : false} animate={{ backgroundColor: "#FFFBF1" }} transition={{ duration: 0.9 }}>
      <div>
        <div className="tiny bold">总资产</div>
        <div className="display num" style={{ fontSize: 32, lineHeight: 1.05 }}><span className={total < 0 ? "down" : ""}>{total}</span><small style={{ fontSize: 15 }}> 万</small></div>
        <div className="row gap6 mt4">
          <span className="tiny bold">{label}</span>
          {Array.from({ length: Math.max(3, shares) }).map((_, i) => (
            <motion.i key={i} animate={{ scale: i < shares ? 1 : 0.7 }} className={"acct-coin" + (i < shares ? " f" : "")} />
          ))}
          <b className="small">{shares} 份</b>
        </div>
      </div>
      <div style={{ textAlign: "right" }}>
        <div className="tiny bold">这一场盈亏</div>
        <motion.div className={"display num " + cls} style={{ fontSize: 40, lineHeight: 1 }} initial={dir ? { scale: 1.3 } : false} animate={{ scale: 1 }}>
          {pnl > 0 ? "+" : pnl < 0 ? "−" : "±"}{Math.abs(pnl)}<small style={{ fontSize: 16 }}> 万</small>
        </motion.div>
        <div className={"tiny bold " + cls}>{pnl > 0 ? "+" : pnl < 0 ? "−" : ""}{Math.abs(Math.round((pnl / Math.max(1, g?.money ?? 20)) * 100))}%</div>
      </div>
    </motion.div>
  );
}

export function PlanPrompt({ plan, pctNow, onFollow, onIgnore, shares, note }: { plan: "cut" | "add"; pctNow: number; onFollow: () => void; onIgnore: () => void; shares: number; note?: string }) {
  return (
    <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="card" style={{ background: "#FFF4D6", borderColor: "#D4432A", boxShadow: "4px 4px 0 #D4432A" }}>
      <div className="row between"><b className="h3">{plan === "cut" ? "止损线到了" : "补仓线到了"}</b><span className="pill" style={{ background: "#D4432A", color: "#fff" }}>你定的：{plan === "cut" ? "跌了就走" : "跌了就加"}</span></div>
      <div className="row gap8 mt4" style={{ alignItems: "baseline" }}>
        <span className="display num down" style={{ fontSize: 44, lineHeight: 1 }}>{pctNow.toFixed(1)}%</span>
        <span className="small">从买入价算</span>
      </div>
      {note && <div className="tiny mt4">{note}</div>}
      <div className="row gap8 mt8">
        <button className="btn ghost grow" onClick={onIgnore}>先不了</button>
        <button className="btn primary grow" onClick={onFollow}>{plan === "cut" ? "照计划卖出" : "照计划加仓"}</button>
      </div>
      <div className="tiny mt8">照做 +1★；不照做，记一次“临场改主意”。</div>
    </motion.div>
  );
}
