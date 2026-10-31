import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { ART, SEASONS, sceneById, type SceneId } from "../data";
import { CHANCE, DATAPORT, RULES, pickN, ruleView } from "../game/cards";
import { sp } from "../game/meta";
import { cur, useGame, type TileKind } from "../game/store";
import { buzz, sfx } from "../lib/sound";
import { Hud } from "../ui/Hud";
import { Fade, Sheet, sleep, SpeciesAvatar } from "../ui/kit";
import { Rich } from "../ui/Term";

const TILES: TileKind[] = ["supply", "chance", "research", "dataport", "calm"];
const TILE_CN: Record<string, string> = { supply: "补给站", chance: "机会", research: "研究所", dataport: "数据港口", calm: "冷静亭", door: "名场面之门" };
const TILE_DESC: Record<string, string> = {
  supply: "拿 1 研究点",
  chance: "抽一张机会牌，二选一",
  research: "摸两张规则牌，留一张",
  dataport: "读一段 panda_data 代码，答对拿 1 研究点",
  calm: "坐下：这一季不能选最激进的 A，但免费翻一张证据卡",
};
const TILE_SHORT: Record<string, string> = { supply: "+1 研究点", chance: "答一题", research: "拿规则牌", dataport: "读代码", calm: "免费看证据" };

/** 环形 28 格：0 左上角起点，顺时针 */
export function cellRC(p: number): [number, number] {
  if (p <= 7) return [0, p];
  if (p <= 14) return [p - 7, 7];
  if (p <= 21) return [7, 7 - (p - 14)];
  return [7 - (p - 21), 0];
}
export const seasonStart = (s: number) => s * 7;

function Pawn({ pos, hop }: { pos: number; hop: number }) {
  const [r, c] = cellRC(pos % 28);
  return (
    <motion.div style={{ position: "absolute", width: "9%", aspectRatio: "0.8", zIndex: 6, pointerEvents: "none", left: 0, top: 0 }}
      animate={{ left: `${((c + 0.5) / 8) * 100 - 4.5}%`, top: `${((r + 0.5) / 8) * 100 - 7}%` }}
      transition={{ type: "spring", stiffness: 380, damping: 26 }}>
      <motion.div key={hop} initial={{ y: 0 }} animate={{ y: [0, -16, 0] }} transition={{ duration: 0.28 }}>
        <svg viewBox="0 0 40 50" width="100%">
          <ellipse cx="20" cy="46" rx="12" ry="3.5" fill="rgba(0,0,0,.3)" />
          <path d="M20 3 C31 3 37 20 37 30 C37 40 29 46 20 46 C11 46 3 40 3 30 C3 20 9 3 20 3 Z" fill="#FBF4E4" stroke="#2A2A1C" strokeWidth="3" />
          <path d="M8 27 l5 -4 l5 5 l5 -5 l5 5 l5 -4" fill="none" stroke="#D4432A" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="15" cy="16" r="3" fill="#C79A2E" />
        </svg>
      </motion.div>
    </motion.div>
  );
}

function Board({ pos, hop, seasonIdx }: { pos: number; hop: number; seasonIdx: number }) {
  const cells = useMemo(() => {
    const out: { p: number; r: number; c: number; kind: string; season: number }[] = [];
    for (let p = 0; p < 28; p++) {
      const [r, c] = cellRC(p);
      const season = Math.floor(p / 7);
      const k = p % 7;
      const kind = k === 0 ? (p === 0 ? "start" : "station") : k === 6 ? "door" : TILES[k - 1];
      out.push({ p, r, c, kind, season });
    }
    return out;
  }, []);
  return (
    <div className="board-wrap" style={{ width: "min(100%, 440px)" }}>
      <div className="board">
        {cells.map((x) => {
          const sid = SEASONS[x.season].id;
          const active = x.season === seasonIdx;
          return (
            <div key={x.p} className={`cell s-${sid} ${x.kind === "door" ? "door" : ""} ${x.kind === "station" || x.kind === "start" ? "corner" : ""}`}
              style={{ gridRow: x.r + 1, gridColumn: x.c + 1, opacity: active || x.kind === "station" || x.kind === "start" ? 1 : 0.72, boxShadow: active && x.kind !== "door" ? "inset 0 -5px 0 var(--season)" : undefined }}>
              {x.kind === "door" ? (
                <span className="display" style={{ color: "#fff8ec", fontSize: 18, textShadow: "1px 1px 0 #2A2A1C" }}>门</span>
              ) : (
                <img src={ART(`tile_${x.kind}`)} alt={TILE_CN[x.kind] || ""} loading="lazy" />
              )}
              {x.kind !== "door" && x.kind !== "station" && x.kind !== "start" && <span className="no">{x.p % 7}</span>}
            </div>
          );
        })}
        <div className="board-center">
          <img src={ART("board_bg_1")} alt="" />
          <div className="abs-fill" style={{ display: "grid", placeItems: "center" }}>
            <div style={{ textAlign: "center", background: "rgba(251,244,228,.92)", border: "2px solid #2A2A1C", borderRadius: 12, padding: "8px 14px", boxShadow: "3px 3px 0 #2A2A1C" }}>
              <div className="kicker" style={{ letterSpacing: ".1em" }}>第 {seasonIdx + 1} 季 / 4</div>
              <div className="display" style={{ fontSize: 26 }}>{SEASONS[seasonIdx]?.cn} · {SEASONS[seasonIdx]?.name}</div>
            </div>
          </div>
        </div>
      </div>
      <Pawn pos={pos} hop={hop} />
    </div>
  );
}

function Die({ v, red, picked, rolling, onClick }: { v: number; red?: boolean; picked?: boolean; rolling?: boolean; onClick?: () => void }) {
  const pips: Record<number, number[]> = { 1: [4], 2: [0, 8], 3: [0, 4, 8], 4: [0, 2, 6, 8], 5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8] };
  return (
    <motion.button className={"die" + (red ? " red" : "") + (picked ? " pick" : "")} onClick={onClick}
      animate={rolling ? { rotate: [0, 120, 260, 380, 520, 720], y: [0, -40, 0, -20, 0] } : { rotate: 0, y: picked ? -8 : 0 }}
      transition={{ duration: rolling ? 0.9 : 0.25 }}>
      {Array.from({ length: 9 }).map((_, i) => <i key={i} style={{ visibility: pips[v]?.includes(i) ? "visible" : "hidden" }} />)}
    </motion.button>
  );
}

export function MapScreen({ onEnterScene }: { onEnterScene: () => void }) {
  const { g, update } = useGame();
  const [hop, setHop] = useState(0);
  const [dice, setDice] = useState<[number, number] | null>(null);
  const [rolling, setRolling] = useState(false);
  const [diceOpen, setDiceOpen] = useState(false);
  const [moving, setMoving] = useState(false);
  const [tile, setTile] = useState<TileKind | null>(null);
  const [doorOpen, setDoorOpen] = useState(false);
  const [banner, setBanner] = useState(true);
  const [rerolling, setRerolling] = useState(false);
  const seasonIdx = g?.seasonIdx ?? 0;
  useEffect(() => {
    setBanner(true);
    const t = setTimeout(() => setBanner(false), 1900);
    return () => clearTimeout(t);
  }, [seasonIdx]);
  if (!g) return null;
  const rec = cur(g);
  const season = SEASONS[g.seasonIdx];
  const start = seasonStart(g.seasonIdx);
  const landed = rec.tile;

  async function walk(to: number) {
    setMoving(true);
    const from = useGame.getState().g?.pos ?? start;
    for (let p = from + 1; p <= to; p++) {
      update((x) => void (x.pos = p));
      setHop((h) => h + 1);
      sfx.hop();
      await sleep(260);
    }
    sfx.land();
    setMoving(false);
  }

  async function roll() {
    setDiceOpen(true);
    setRolling(true);
    sfx.dice();
    await sleep(900);
    const d: [number, number] = [1 + Math.floor(Math.random() * 6), 1 + Math.floor(Math.random() * 6)];
    setDice(d);
    setRolling(false);
    update((x) => void (cur(x).dice = d));
  }

  async function pick(v: number) {
    const reroll = rerolling;
    setRerolling(false);
    setDiceOpen(false);
    update((x) => {
      cur(x).picked = v;
      if (reroll) cur(x).rerolled = true;
    });
    await sleep(250);
    if (reroll && v === 5) {
      await walk(start + 5);
      update((x) => {
        cur(x).tile = "calm";
        cur(x).calm = "sat";
        cur(x).freeEvidence = 1;
      });
      setTile("calm");
      return;
    }
    if (v === 6) {
      await walk(start + 6);
      update((x) => {
        x.rp += 1;
        cur(x).rpGained += 1;
        cur(x).tile = "door";
      });
      sfx.coin();
      setDoorOpen(true);
      return;
    }
    await walk(start + v);
    const kind = TILES[v - 1];
    update((x) => void (cur(x).tile = kind));
    setTile(kind);
  }

  async function goDoor() {
    setTile(null);
    await walk(start + 6);
    setDoorOpen(true);
  }

  async function calmSkip() {
    setTile(null);
    update((x) => {
      cur(x).calm = "skip";
      x.pos = start;
    });
    setRerolling(true);
    await roll();
  }

  const doors = season.doors.map((id) => sceneById(id)!).filter(Boolean);
  return (
    <div className={`screen s-${season.id}`}>
      <Hud />
      <div style={{ padding: "6px 12px 0" }}>
        <Board pos={g.pos} hop={hop} seasonIdx={g.seasonIdx} />
      </div>
      <div className="pad col gap12" style={{ paddingTop: 14 }}>
        <div className="row between">
          <div>
            <div className="kicker">第 {g.seasonIdx + 1} 季 · {season.cn}</div>
            <div className="h3">{!landed ? "掷两颗骰子，选一个点数" : landed === "door" ? "到门口了" : `落在：${TILE_CN[landed]}`}</div>
          </div>
          <div className="row gap4">{g.opponents.map((id) => <SpeciesAvatar key={id} id={id} size={34} />)}</div>
        </div>
        {!landed && (
          <div className="card flat small" style={{ background: "#FFF6DE" }}>
            掷两颗骰子，挑一个点数走过去，拿到格子上的东西，再去名场面之门。
            <div className="row wrap gap6 mt8">
              {TILES.map((t, i) => <span key={t} className="pill">{i + 1} {TILE_CN[t]} · <span style={{ fontWeight: 500 }}>{TILE_SHORT[t]}</span></span>)}
              <span className="pill season">6 直达门口 · +1 研究点</span>
            </div>
          </div>
        )}
        {!landed && <button className="btn season big block pulse" disabled={moving || banner} onClick={roll}>🎲 掷骰子</button>}
        {landed && landed !== "door" && !tile && !doorOpen && (
          <button className="btn season big block" disabled={moving} onClick={goDoor}>前往名场面之门 →</button>
        )}
        {landed === "door" && !doorOpen && <button className="btn season big block" onClick={() => setDoorOpen(true)}>推开门</button>}
      </div>

      <AnimatePresence>
        {banner && (
          <motion.div className="abs-fill" style={{ position: "fixed", zIndex: 80, display: "grid", placeItems: "center", pointerEvents: "none" }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.div initial={{ scale: 0.6, rotate: -6 }} animate={{ scale: 1, rotate: -3 }} exit={{ scale: 1.3, opacity: 0 }} transition={{ type: "spring", stiffness: 260, damping: 16 }}
              className="card" style={{ background: "var(--season)", color: "#fff8ec", padding: "18px 30px", textAlign: "center", boxShadow: "6px 6px 0 #2A2A1C" }}>
              <div className="kicker" style={{ color: "#fff8ec" }}>第 {g.seasonIdx + 1} 季</div>
              <div className="display" style={{ fontSize: 54 }}>{season.cn} · {season.name}</div>
              <div className="small bold">本季预算 +1 研究点（用来看证据）</div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <Sheet open={diceOpen} dismissable={false}>
        <div className="center">
          <div className="kicker">{rolling ? "骰子在滚……" : rerolling ? "不坐：从本季起点重新数" : "选一个点数"}</div>
          <div className="dice-row mt16 mb12">
            <Die v={dice?.[0] || 1} rolling={rolling} onClick={() => !rolling && dice && pick(dice[0])} />
            <Die v={dice?.[1] || 6} red rolling={rolling} onClick={() => !rolling && dice && pick(dice[1])} />
          </div>
          {dice && !rolling && (
            <Fade>
              <div className="row gap8 mt8">
                {dice.map((v, i) => (
                  <button key={i} className="btn block" style={{ flexDirection: "column", gap: 2, padding: "10px 8px" }} onClick={() => pick(v)}>
                    <b style={{ fontSize: 18 }}>走 {v} 步</b>
                    <span className="tiny" style={{ color: "inherit" }}>{v === 6 ? "直达门口 · +1 研究点" : rerolling && v === 5 ? "冷静亭 · 必须坐下" : `${TILE_CN[TILES[v - 1]]} · ${TILE_SHORT[TILES[v - 1]]}`}</span>
                  </button>
                ))}
              </div>
              <div className="tiny mt8">{dice[0] !== dice[1] ? (rerolling ? "落到哪格执行哪格；再选冷静亭就必须坐下" : "两颗骰子选一个：你想去哪一格？") : "两颗一样，只能走这一格"}</div>
            </Fade>
          )}
        </div>
      </Sheet>

      <TileSheet kind={tile} onClose={goDoor} onCalmSkip={calmSkip} />

      <Sheet open={doorOpen} dismissable={false}>
        <div className="kicker">{season.cn} · 名场面之门</div>
        <h3 className="h2 mt4">{doors.length > 1 ? "两扇门，选一扇" : "门后是一个真实的历史时刻"}</h3>
        <p className="small muted mt8">名字和日期都被藏起来了。你只能用当时看得到的信息做决定。</p>
        <div className="col gap12 mt12">
          {doors.map((s) => (
            <motion.button key={s.id} whileTap={{ scale: 0.97 }} className="card" style={{ textAlign: "left", cursor: "pointer", padding: 0, overflow: "hidden", display: "grid", gridTemplateColumns: "92px 1fr" }}
              onClick={() => {
                sfx.reveal();
                update((x) => {
                  cur(x).scene = s.id as SceneId;
                  cur(x).door = s.door;
                  x.phase = "scene";
                  x.step = "blind";
                });
                setDoorOpen(false);
                onEnterScene();
              }}>
              <div style={{ background: `var(--${s.season})`, display: "grid", placeItems: "center", borderRight: "2px solid #2A2A1C", position: "relative" }}>
                <img src={ART(`blind_${s.id}`)} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(3px) saturate(.8)", position: "absolute", inset: 0 }} />
                <span className="display" style={{ position: "relative", fontSize: 44, color: "#fff8ec", textShadow: "2px 2px 0 #2A2A1C" }}>{s.door}</span>
              </div>
              <div style={{ padding: 12 }}>
                <div className="bold">{s.door_hint}</div>
                <div className="tiny mt4">{s.door === "B" ? (s.id === "squant" ? "量化门：规则和因子的世界" : "期货门：读懂产品说明书") : "股票门：看行情，凭判断"}</div>
                <div className="row gap6 mt8"><span className="pill">{s.market}</span>{s.tier === "P1" && <span className="pill warn">进阶</span>}</div>
              </div>
            </motion.button>
          ))}
        </div>
      </Sheet>
    </div>
  );
}

function TileSheet({ kind, onClose, onCalmSkip }: { kind: TileKind | null; onClose: () => void; onCalmSkip: () => void }) {
  return (
    <Sheet open={!!kind} dismissable={false}>
      {kind && (
        <div>
          <div className="row gap12">
            <img src={ART(`tile_${kind}`)} alt="" style={{ width: 74, height: 74 }} />
            <div>
              <div className="kicker">小格子</div>
              <div className="h2">{TILE_CN[kind]}</div>
              <div className="small muted">{TILE_DESC[kind]}</div>
            </div>
          </div>
          <div className="stripe mt12 mb12" />
          {kind === "supply" && <Supply onDone={onClose} />}
          {kind === "chance" && <Chance onDone={onClose} />}
          {kind === "research" && <Research onDone={onClose} />}
          {kind === "dataport" && <DataPort onDone={onClose} />}
          {kind === "calm" && <Calm onDone={onClose} onSkip={onCalmSkip} />}
        </div>
      )}
    </Sheet>
  );
}

function Supply({ onDone }: { onDone: () => void }) {
  const { update } = useGame();
  const [got, setGot] = useState(false);
  return (
    <div className="center">
      <motion.div className="coin" style={{ margin: "6px auto", background: "radial-gradient(circle at 35% 30%, #ffe9a8, #C79A2E 70%)" }} animate={got ? { y: [-0, -60], opacity: [1, 0], scale: [1, 0.4] } : { rotateY: [0, 360] }} transition={got ? { duration: 0.6 } : { repeat: Infinity, duration: 2.2, ease: "linear" }}>
        <span className="display" style={{ fontSize: 34 }}>研</span>
      </motion.div>
      <p className="body">研究点是你的预算：每翻一张证据卡要花 1 点。<br />研究点很紧，要自己挑在哪一场多下功夫。</p>
      <button className="btn season big block" onClick={async () => {
        if (!got) {
          setGot(true);
          sfx.coin();
          update((x) => {
            x.rp += 1;
            cur(x).rpGained += 1;
          });
          await sleep(650);
        }
        onDone();
      }}>收下 +1 研究点</button>
    </div>
  );
}

function Chance({ onDone }: { onDone: () => void }) {
  const { g, update } = useGame();
  const used = new Set(g!.seasons.map((r) => r.chance?.id).filter(Boolean));
  const [card] = useState(() => pickN(CHANCE.filter((c) => !used.has(c.id)), 1)[0] || CHANCE[0]);
  const [ans, setAns] = useState<number | null>(null);
  const [open, setOpen] = useState(false);
  if (!open) {
    return (
      <div style={{ perspective: 900 }}>
        <motion.button className="chance-back" onClick={() => { sfx.paper(); buzz(15); setOpen(true); }}
          initial={{ y: -60, rotate: -8, opacity: 0 }} animate={{ y: 0, rotate: [0, -2, 2, 0], opacity: 1 }} transition={{ y: { type: "spring", stiffness: 220, damping: 16 }, rotate: { delay: 0.5, duration: 0.6, repeat: Infinity, repeatDelay: 1.2 } }}>
          <span className="chance-q">?</span>
          <b>翻开机会牌</b>
          <span className="tiny" style={{ color: "inherit", opacity: 0.8 }}>一个问题，两个答案，没有对错</span>
        </motion.button>
      </div>
    );
  }
  return (
    <motion.div initial={{ rotateY: -90, opacity: 0 }} animate={{ rotateY: 0, opacity: 1 }} transition={{ duration: 0.35 }} style={{ transformPerspective: 900 }}>
      <div className="pill dark">{card.dimension}</div>
      <p className="h3 mt8" style={{ lineHeight: 1.35 }}>{card.q}</p>
      <div className="col gap8 mt12">
        {card.a.map((a, i) => (
          <motion.button key={i} className={"opt" + (ans === i ? " on" : "")} style={{ gridTemplateColumns: "38px 1fr" }} disabled={ans != null && ans !== i}
            onClick={() => {
              if (ans != null) return;
              setAns(i);
              sfx.paper();
              update((x) => void (cur(x).chance = { id: card.id, answer: i, species: a.species }));
            }}>
            <span className="key">{"甲乙"[i] || i + 1}</span>
            <span>{a.text}</span>
          </motion.button>
        ))}
      </div>
      <AnimatePresence>
        {ans != null && (
          <motion.div initial={{ rotateY: 90, opacity: 0 }} animate={{ rotateY: 0, opacity: 1 }} transition={{ duration: 0.5 }} className="card mt12 row gap12" style={{ background: "#FFF4D6" }}>
            <SpeciesAvatar id={card.a[ans].species} size={54} />
            <div>
              <div className="tiny">翻到背面：这个回答像</div>
              <div className="h3">{sp(card.a[ans].species).cn}</div>
              <div className="tiny">记 1 个物种图标。机会牌没有对错。</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      <button className="btn season big block mt12" disabled={ans == null} onClick={onDone}>收好，去门口</button>
    </motion.div>
  );
}

function Research({ onDone }: { onDone: () => void }) {
  const { g, update } = useGame();
  const [offer] = useState(() => pickN(RULES.filter((r) => !g!.rules.includes(r.id)), 2));
  const revealed = g!.seasons.filter((r) => r.stars).map((r) => r.scene!);
  const [keep, setKeep] = useState<string | null>(null);
  return (
    <div>
      <p className="small">两张规则牌，留一张。之后做决定时，可以把它当作理由，但用了就必须照规则做。带“真实对应”的，是 PandaAI 里 Qube 的真实策略模板。</p>
      <div className="row gap8 mt8" style={{ alignItems: "stretch" }}>
        {offer.map((r, i) => (
          <motion.button key={r.id} initial={{ y: 30, opacity: 0, rotate: i ? 4 : -4 }} animate={{ y: 0, opacity: 1, rotate: keep === r.id ? 0 : i ? 2 : -2 }} transition={{ delay: i * 0.12 }}
            onClick={() => { sfx.tap(); setKeep(r.id); }}
            className="card" style={{ flex: 1, textAlign: "left", cursor: "pointer", background: keep === r.id ? "#2A2A1C" : "#FBF4E4", color: keep === r.id ? "#FBF4E4" : undefined, padding: 12 }}>
            <div className="pill" style={{ background: "#C79A2E", color: "#2A2A1C" }}>{r.does || "规则"}</div>
            <div className="h3 mt8">{ruleView(r, revealed).name}</div>
            <div className="small mt4" style={{ opacity: 0.9 }}><Rich text={r.text} max={2} /></div>
            {r.real && <div className="tiny mt8" style={{ color: keep === r.id ? "#F3D27F" : undefined }}>真实对应：{r.real.name}</div>}
          </motion.button>
        ))}
      </div>
      <button className="btn season big block mt12" disabled={!keep} onClick={() => {
        sfx.stamp();
        update((x) => {
          x.rules.push(keep!);
          cur(x).ruleKept = keep!;
          cur(x).rulesOffered = offer.map((o) => o.id);
        });
        onDone();
      }}>留下这张</button>
    </div>
  );
}

function DataPort({ onDone }: { onDone: () => void }) {
  const { g, update } = useGame();
  const used = new Set(g!.seasons.map((r) => (typeof r.dataport === "object" ? r.dataport.id : "")).filter(Boolean));
  const [card] = useState(() => pickN(DATAPORT.filter((c) => !used.has(c.id)), 1)[0] || DATAPORT[0]);
  const [ans, setAns] = useState<number | null>(null);
  const right = ans === card.correct;
  return (
    <div>
      <div className="small bold">{card.title}</div>
      <pre style={{ background: "#1f2a26", color: "#d9f0c8", borderRadius: 12, border: "2px solid #2A2A1C", padding: 12, fontSize: 12.5, lineHeight: 1.55, overflowX: "auto", margin: "8px 0" }}>{card.code}</pre>
      <p className="bold">{card.q}</p>
      <div className="col gap8">
        {card.a.map((a, i) => (
          <button key={i} className={"opt" + (ans === i ? " on" : "")} style={{ gridTemplateColumns: "38px 1fr", background: ans != null && i === card.correct ? "#E3F0D9" : undefined }} disabled={ans != null}
            onClick={() => {
              setAns(i);
              const ok = i === card.correct;
              ok ? sfx.gain() : sfx.loss();
              update((x) => {
                x.dataportSeen += 1;
                cur(x).dataport = { id: card.id, answer: i, correct: ok };
                if (ok) {
                  x.dataportRight += 1;
                  x.rp += 1;
                  cur(x).rpGained += 1;
                }
              });
            }}>
            <span className="key">{"ABC"[i]}</span><span>{a}</span>
          </button>
        ))}
      </div>
      {ans != null && (
        <Fade>
          <div className="card mt12" style={{ background: right ? "#E3F0D9" : "#FBE3DC" }}>
            <b>{right ? "答对了：+1 研究点，记一次“数据”" : "差一点"}</b>
            <div className="small mt4">{card.explain}</div>
            {card.variant && <div className="tiny mt8" style={{ background: "#fff", border: "1.5px dashed #77745A", borderRadius: 8, padding: "6px 8px" }}>回家试试：把 <code>{card.variant.param}</code> 从 <code>{card.variant.from}</code> 改成 <code>{card.variant.to}</code>，{card.variant.what_you_see}。</div>}
            <div className="tiny mt4">代码用的是 Panda Data 的 Python 接口（panda_data）。</div>
          </div>
        </Fade>
      )}
      <div className="row gap8 mt12">
        {ans == null && <button className="btn ghost" onClick={() => { update((x) => void (cur(x).dataport = "skip")); onDone(); }}>跳过</button>}
        <button className="btn season big grow" disabled={ans == null} onClick={onDone}>去门口</button>
      </div>
    </div>
  );
}

function Calm({ onDone, onSkip }: { onDone: () => void; onSkip: () => void }) {
  const { g, update } = useGame();
  const forced = cur(g!).calm === "sat";
  return (
    <div>
      <p className="body">{forced ? "又落到冷静亭：这次必须坐下。" : "要不要在这里坐一会儿？"}</p>
      <div className="col gap8 mt8">
        <button className="card" style={{ textAlign: "left", cursor: "pointer" }} onClick={() => {
          sfx.tap();
          update((x) => {
            cur(x).calm = "sat";
            cur(x).freeEvidence = 1;
          });
          onDone();
        }}>
          <b>坐下</b>
          <div className="small muted mt4">这一季不能选最激进的 A，但可以免费翻一张证据卡。</div>
        </button>
        {!forced && (
          <button className="card" style={{ textAlign: "left", cursor: "pointer" }} onClick={onSkip}>
            <b>不坐，马上再掷一次</b>
            <div className="small muted mt4">落到哪格执行哪格；再落到冷静亭，就必须坐下。</div>
          </button>
        )}
      </div>
    </div>
  );
}
