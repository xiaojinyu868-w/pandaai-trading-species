import { motion } from "framer-motion";
import { ART, SCENES, type SceneId } from "../data";
import { playedIds, suggestNext } from "../game/adaptive";
import { newSeason, useGame, type Game } from "../game/store";
import { sfx } from "../lib/sound";
import { Hud } from "../ui/Hud";

const ORDER = ["s924", "s2015", "smt", "scb", "squant", "soil"];

/** 快速版：进入一个名场面。已经玩过的季记录保留，新开一条。 */
export function enterQuickScene(x: Game, id: SceneId) {
  const s = SCENES.find((y) => y.id === id)!;
  let r = x.seasons[x.seasonIdx];
  if (r.scene && r.option) {
    x.seasonIdx = x.seasons.length;
    x.seasons.push(newSeason(s.season));
    r = x.seasons[x.seasonIdx];
    x.rp += 2;
  }
  r.season = s.season;
  r.scene = id;
  r.door = s.door;
  x.phase = "scene";
  x.step = "blind";
  delete x.finishedAt;
}

export function QuickPick() {
  const { g, update } = useGame();
  if (!g) return null;
  const played = new Set(playedIds(g));
  const first = played.size === 0;
  const next = first ? null : suggestNext(g);
  const list = ORDER.map((id) => SCENES.find((s) => s.id === id)!).filter((s) => s && !played.has(s.id));
  return (
    <div className="screen">
      <Hud title={first ? "快速版" : `第 ${played.size + 1} 场`} />
      <div className="pad">
        <div className="kicker">{first ? "快速版 · 选一个历史时刻" : "再来一场 · 让画像更准"}</div>
        <h2 className="h2 mt4">{first ? "你想回到哪一天？" : "下一场去哪？"}</h2>
        <div className="stripe mt8" style={{ width: 80 }} />
        <p className="small muted mt8">{first ? "名字和日期都藏起来了。挑一天，回到那个时刻。" : next?.why}</p>
        <div className="col gap10 mt12">
          {list.map((s, i) => {
            const rec = next?.scene.id === s.id;
            return (
              <motion.button key={s.id} className={`card s-${s.season}`} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} whileTap={{ scale: 0.97 }}
                style={{ textAlign: "left", cursor: "pointer", padding: 0, overflow: "hidden", display: "grid", gridTemplateColumns: "96px 1fr", boxShadow: rec ? "5px 5px 0 #D4432A" : undefined, borderWidth: rec ? 3 : undefined }}
                onClick={() => { sfx.reveal(); update((x) => enterQuickScene(x, s.id)); }}>
                <div style={{ position: "relative", background: "var(--season)", borderRight: "2px solid #2A2A1C", minHeight: 96 }}>
                  <img src={ART(`blind_${s.id}`)} alt="" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
                </div>
                <div style={{ padding: "10px 12px" }}>
                  <div className="row gap6 wrap">
                    <span className="pill" style={{ background: "var(--season)", color: "#fff8ec" }}>{s.season_cn} · {s.season_name}</span>
                    {rec && <span className="pill warn">推荐</span>}
                    {s.tier === "P1" && <span className="pill">进阶</span>}
                  </div>
                  <div className="bold mt4">{s.blind.headline}</div>
                  <div className="tiny mt4">{s.door_hint}</div>
                </div>
              </motion.button>
            );
          })}
        </div>
        <p className="tiny center mt12">一场约 3 分钟，玩完就出画像。</p>
      </div>
    </div>
  );
}
