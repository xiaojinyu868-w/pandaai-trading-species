import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { SEASONS } from "../data";
import { useGame } from "../game/store";
import { isMuted, setMuted } from "../lib/sound";
import { Counter, RP, Sheet } from "./kit";
import { openTerm } from "./Term";

export function Hud({ title }: { title?: string }) {
  const { g, reset } = useGame();
  const nav = useNavigate();
  const [menu, setMenu] = useState(false);
  const [muted, setM] = useState(isMuted());
  const prev = useRef<number | undefined>(g?.money);
  const [delta, setDelta] = useState<{ n: number; k: number } | null>(null);
  useEffect(() => {
    if (g == null) return;
    const was = prev.current;
    prev.current = g.money;
    if (was == null || was === g.money) return;
    setDelta({ n: g.money - was, k: Date.now() });
    const t = setTimeout(() => setDelta(null), 1800);
    return () => clearTimeout(t);
  }, [g?.money]);
  if (!g) return null;
  const stars = g.seasons.reduce((a, r) => a + (r.stars?.total || 0), 0);
  return (
    <>
      <div className="hud">
        <button className="btn ghost sm" style={{ padding: "4px 8px", border: "none" }} onClick={() => setMenu(true)} aria-label="菜单">☰</button>
        <div className="stat money-stat" role="button" onClick={() => openTerm("资金", true)}>
          <small className="term">资金</small>
          <span><Counter value={g.money} className={g.money < 0 ? "down" : ""} /><small className="unit">万</small></span>
          <AnimatePresence>
            {delta && (
              <motion.span key={delta.k} className={"hud-delta " + (delta.n > 0 ? "up" : "down")} initial={{ opacity: 0, y: -6, scale: 0.6 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 10 }} transition={{ type: "spring", stiffness: 420, damping: 18 }}>
                {delta.n > 0 ? "+" : "−"}{Math.round(Math.abs(delta.n) * 10) / 10} 万
              </motion.span>
            )}
          </AnimatePresence>
        </div>
        <div className="stat" role="button" onClick={() => openTerm("研究点", true)}><small className="term">研究点</small><RP n={g.rp} compact /></div>
        <div className="stat" role="button" onClick={() => openTerm("方法星", true)}><small className="term">方法星</small>★{stars}</div>
        <div className="grow" />
        <span className="pill season hud-title">{title || SEASONS.find((s) => s.id === g.seasons[g.seasonIdx]?.season)?.cn || SEASONS[g.seasonIdx]?.cn}</span>
      </div>
      <Sheet open={menu} onClose={() => setMenu(false)}>
        <div className="h3">菜单</div>
        <div className="col gap8 mt12">
          <button className="btn block" onClick={() => { setMenu(false); nav("/"); }}>回到首页（进度自动保存）</button>
          <button className="btn block" onClick={() => { setMenu(false); nav("/atlas"); }}>物种图鉴</button>
          <button className="btn block" onClick={() => { setMenu(false); nav("/about"); }}>数据来源与说明</button>
          <button className="btn block" onClick={() => { setMuted(!muted); setM(!muted); }}>{muted ? "🔇 声音已关，点一下打开" : "🔊 声音已开，点一下关闭"}</button>
          <button className="btn ghost block" onClick={() => { if (confirm("放弃这一局，重新开始？")) { reset(); setMenu(false); nav("/"); } }}>放弃这一局</button>
        </div>
        <div className="card flat mt12 small" style={{ background: "#FFF6DE" }}>
          <b>三样东西，各管一件事</b>
          <div className="mt4"><b>资金</b>：模拟资金，开局 20 万，只看结果。</div>
          <div><b>研究点</b>：翻证据卡的预算，每张 1 个。</div>
          <div><b>方法星</b>：看你怎么想，和赚没赚无关。</div>
          <div className="tiny mt4">正文里带虚线的词都能点开，看一句人话解释。</div>
        </div>
        <p className="tiny mt12">投资者教育游戏，不构成投资建议。游戏记录只保存在这台手机的浏览器里。</p>
      </Sheet>
    </>
  );
}
