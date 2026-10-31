import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ART, SEASONS } from "../data";
import { OPPONENT_SETS, PICKABLE, sp, type SpeciesId } from "../game/meta";
import { useGame } from "../game/store";
import { sfx } from "../lib/sound";
import { MuteButton, SpeciesAvatar } from "../ui/kit";
import { Ride } from "../ride/Ride";
import { Help } from "../ui/Term";
import { useArcade } from "../arcade/store";

export function Home() {
  const nav = useNavigate();
  const { g, start, startQuick } = useGame();
  const resumable = g && g.phase !== "ending" && g.source === "h5";
  const arc = useArcade();
  const arcOn = arc.stage !== "final" && (arc.idx > 0 || arc.stage !== "cold");
  return (
    <div className="screen" style={{ background: "#3d7f92" }}>
      <motion.img src={ART("opening")} alt="" className="abs-fill" style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 30%" }}
        initial={{ scale: 1.12 }} animate={{ scale: 1 }} transition={{ duration: 2.4, ease: "easeOut" }} />
      <div className="abs-fill" style={{ background: "linear-gradient(180deg, rgba(23,60,75,.55) 0%, rgba(23,60,75,.32) 30%, rgba(23,60,75,0) 46%, rgba(0,0,0,0) 60%, rgba(42,42,28,.55) 100%)" }} />
      <div style={{ position: "absolute", right: 10, top: 10, zIndex: 5 }}><MuteButton /></div>
      <div className="pad" style={{ position: "relative", zIndex: 2, paddingTop: 14 }}>
        <motion.div initial={{ opacity: 0, y: -18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.7 }}>
          <span className="panda-tag">PandaAI · 交易人格测评</span>
          <h1 className="display" style={{ fontSize: 46, color: "#FBF4E4", margin: "8px 0 0", textShadow: "4px 4px 0 #2A2A1C", lineHeight: 0.98 }}>
            交易物种起源
          </h1>
          <div style={{ width: 120, height: 6, background: "#C79A2E", margin: "8px 0 8px", border: "2px solid #2A2A1C" }} />
          <p className="lead home-lead" style={{ color: "#FBF4E4", maxWidth: 310, textShadow: "0 1px 8px rgba(0,0,0,.45)", margin: 0, fontWeight: 600 }}>
            回到真实的金融史时刻，日期被藏起来。<br />你怎么做决定，就会孵出什么物种。
          </p>
        </motion.div>
      </div>
      <div className="grow" />
      <motion.div className="pad" style={{ position: "relative", zIndex: 2 }} initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.8, type: "spring", damping: 20 }}>
        <div className="card" style={{ padding: 12 }}>
          <Ride />
          {resumable ? (
            <button className="btn primary big block mt12 home-go" onClick={() => { sfx.bell(); nav("/play"); }}>
              继续上一局
              <small>{g!.mode === "quick" ? "3 分钟版" : `走到${SEASONS[g!.seasonIdx]?.cn || "终"}季了`} · 接着玩</small>
            </button>
          ) : (
            <button className="btn primary big block mt12 home-go" onClick={() => { sfx.bell(); start(); nav("/play"); }}>
              开始游戏 · 完整四季
              <small>和桌上那盒同一个游戏 · 约 10 分钟</small>
            </button>
          )}
          <div className="row mt8 gap8">
            <button className="btn grow" style={{ padding: "10px", whiteSpace: "nowrap" }} onClick={() => { sfx.bell(); startQuick(); nav("/play"); }}>先玩一场 · 3 分钟版</button>
            {resumable && <button className="btn grow" style={{ padding: "10px", whiteSpace: "nowrap" }} onClick={() => { sfx.bell(); start(); nav("/play"); }}>重开完整四季</button>}
          </div>
          {g && g.phase === "ending" && (
            <button className="btn block mt8" onClick={() => { sfx.tap(); nav("/play"); }}>再看上一局的画像{g.source === "record" ? "（桌游记录卡）" : ""}</button>
          )}
          <div className="row mt8 gap8">
            <button className="btn sm grow" style={{ padding: "6px 8px", whiteSpace: "nowrap", boxShadow: "none" }} onClick={() => nav("/record")}>桌游记录卡</button>
            <button className="btn sm grow" style={{ padding: "6px 8px", whiteSpace: "nowrap", boxShadow: "none" }} onClick={() => nav("/atlas")}>物种图鉴</button>
            <button className="btn sm grow" style={{ padding: "6px 8px", whiteSpace: "nowrap", boxShadow: "none" }} onClick={() => nav("/demo")}>评委演示台</button>
          </div>
          <div className="tiny center mt8">真实行情来自 Panda Data · 投资者教育游戏，不构成投资建议</div>
        </div>
      </motion.div>
    </div>
  );
}

const PROLOGUE = [
  { k: "1720 年 · 伦敦", t: "南海公司的股票，从年初到夏天涨了好几倍。人人都在排队买，连街边的车夫也在谈股票。" },
  { k: "相传", t: "牛顿也买了。他先赚了一笔，卖掉，又在更高的价格买回去，最后亏了约 2 万英镑。他说：“我能算出天体的运行，却算不出人性的疯狂。”" },
  { k: "这个游戏", t: "不比谁赚得多。你会回到几个真实的历史时刻，日期被藏起来，看看自己是怎么做决定的。" },
];

export function Prologue({ onDone }: { onDone: () => void }) {
  const [i, setI] = useState(0);
  const last = i >= PROLOGUE.length;
  return (
    <div className="screen" style={{ background: "#1e2a26" }}>
      <motion.div style={{ position: "relative", height: "58vh", overflow: "hidden", borderBottom: "3px solid #2A2A1C" }}>
        <motion.img src={ART("prologue")} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 30%" }}
          animate={{ scale: [1.05, 1.12] }} transition={{ duration: 14, ease: "linear" }} />
        <div className="abs-fill" style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 60%, rgba(30,42,38,.9) 100%)" }} />
        <div style={{ position: "absolute", left: 16, top: 14 }}><span className="pill dark">序章 · 南海泡沫</span></div>
      </motion.div>
      <div className="pad grow col" style={{ color: "#FBF4E4", marginTop: -40, position: "relative" }}>
        <AnimatePresence mode="wait">
          {!last ? (
            <motion.div key={i} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.4 }}>
              <div className="kicker" style={{ color: "#F3D27F" }}>{PROLOGUE[i].k}</div>
              <p className="display" style={{ fontSize: 25, lineHeight: 1.4, margin: "10px 0 0" }}>{PROLOGUE[i].t}</p>
            </motion.div>
          ) : (
            <motion.div key="ledgers" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
              <div className="kicker" style={{ color: "#F3D27F" }}>所以，这个游戏记两本账</div>
              <div className="col gap8 mt8">
                <div className="card" style={{ background: "#FBF4E4", color: "#2A2A1C" }}>
                  <div className="row between"><b className="h3">收益账：赚了多少</b><Help k="资金" /></div>
                  <div className="small mt4">按真实的历史行情结算。</div>
                </div>
                <div className="card" style={{ background: "#F3D27F", color: "#2A2A1C" }}>
                  <div className="row between"><b className="h3">方法账：想得怎么样</b><Help k="方法星" /></div>
                  <div className="small mt4">看没看证据、理由对不对得上、有没有计划。和赚没赚无关。</div>
                </div>
                <div className="small" style={{ opacity: 0.9 }}>赚钱可能靠运气，方法不会。你是哪种物种，只看你怎么做决定。</div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div className="grow" />
        <div className="row between mt16">
          <div className="row gap4">{[0, 1, 2, 3].map((k) => <i key={k} style={{ width: k === i ? 22 : 8, height: 8, borderRadius: 4, background: k <= i ? "#F3D27F" : "rgba(255,255,255,.25)", transition: "width .3s" }} />)}</div>
          <button className="btn sun" onClick={() => { sfx.paper(); last ? onDone() : setI(i + 1); }}>{last ? "开始自评" : "继续"}</button>
        </div>
      </div>
    </div>
  );
}

export function SelfPick({ onDone, quick = false }: { onDone: (self: SpeciesId, opp: string[]) => void; quick?: boolean }) {
  const [self, setSelf] = useState<SpeciesId | null>(null);
  const [opp, setOpp] = useState("easy");
  const [stage, setStage] = useState<"self" | "opp">("self");
  return (
    <div className="screen">
      <div className="pad">
        <div className="kicker">{stage === "self" ? "开局 · 先凭感觉选一个" : "开局 · 选对手"}</div>
        <h2 className="h2 mt4">{stage === "self" ? "你觉得你是哪一种？" : "选两位 AI 对手"}</h2>
        <div className="stripe mt8" style={{ width: 80 }} />
        <p className="small muted mt8">{stage === "self" ? "凭感觉选。玩完对照：你以为的你，和实际的你。" : "它们和你走同样的名场面。每次亮牌，都会说出自己的选择和理由，你可以对照着看。"}</p>
      </div>
      {stage === "self" ? (
        <>
          <div className="scroll-x" style={{ display: "flex", gap: 12, padding: "4px 18px 18px", scrollSnapType: "x mandatory" }}>
            {PICKABLE.map((s, i) => (
              <motion.button key={s.id} className="sp-card" onClick={() => { sfx.tap(); setSelf(s.id); }}
                initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }}
                style={{ flex: "0 0 62%", scrollSnapAlign: "center", border: "2px solid #2A2A1C", borderRadius: 16, padding: 0, overflow: "hidden", background: "#FBF4E4", boxShadow: self === s.id ? "0 0 0 4px #D4432A, 5px 5px 0 #2A2A1C" : "3px 3px 0 #2A2A1C", textAlign: "left", position: "relative", cursor: "pointer" }}>
                <img src={ART(`species_${s.id}`)} alt={s.cn} style={{ width: "100%", aspectRatio: "3/3.6", objectFit: "cover", objectPosition: "50% 15%" }} />
                <div style={{ padding: "10px 12px 12px" }}>
                  <div className="row between"><b className="h3">{s.cn}</b><span className="pill">{s.glyph}</span></div>
                  <div className="small bold mt4">{s.tagline}</div>
                  <div className="tiny mt4" style={{ color: "#4A4A33" }}>{s.plain || s.style}</div>
                </div>
                {self === s.id && (
                  <motion.div className="stamp" style={{ left: 16, top: 20, fontSize: 22 }} initial={{ scale: 2.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 400, damping: 18 }}>
                    我觉得是我
                  </motion.div>
                )}
              </motion.button>
            ))}
          </div>
          <div className="pad" style={{ paddingTop: 0 }}>
            <div className="tiny center mb8">选错也没关系。还有一种隐藏物种，玩着才会出现。</div>
            <button className="btn primary big block" disabled={!self} onClick={() => {
              sfx.stamp();
              if (quick) onDone(self!, OPPONENT_SETS[0].ids);
              else setStage("opp");
            }}>
              {self ? `就是${sp(self).cn}` : "左右滑动，选一个"}
            </button>
          </div>
        </>
      ) : (
        <div className="pad col gap12" style={{ paddingTop: 0 }}>
          {OPPONENT_SETS.map((o) => (
            <button key={o.id} className="card" onClick={() => { sfx.tap(); setOpp(o.id); }}
              style={{ textAlign: "left", cursor: "pointer", outline: opp === o.id ? "3px solid #D4432A" : "none", background: opp === o.id ? "#FFF4D6" : undefined }}>
              <div className="row between">
                <div className="row gap8">
                  {o.ids.map((id) => <SpeciesAvatar key={id} id={id} size={50} />)}
                </div>
                <span className={"pill" + (opp === o.id ? " dark" : "")}>{o.cn}</span>
              </div>
              <div className="bold mt8">{o.ids.map((id) => sp(id).cn).join(" + ")}</div>
              <div className="small muted mt4">{o.desc}</div>
            </button>
          ))}
          <button className="btn primary big block mt8" onClick={() => { sfx.bell(); onDone(self!, OPPONENT_SETS.find((x) => x.id === opp)!.ids); }}>出发：春 · 入场</button>
          <button className="btn ghost sm" onClick={() => setStage("self")}>重新自评</button>
        </div>
      )}
    </div>
  );
}
