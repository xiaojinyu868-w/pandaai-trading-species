import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";
import { ART, SEASONS, sceneById } from "../data";
import { retestFor, type RetestCard } from "../game/cards";
import { iconsOf, topOf } from "../game/engine";
import { PICKABLE, sp, type SpeciesId } from "../game/meta";
import { cur, newSeason, useGame } from "../game/store";
import { sfx } from "../lib/sound";
import { Hud } from "../ui/Hud";
import { Fade, Sheet, SpeciesAvatar } from "../ui/kit";
import { Help } from "../ui/Term";
import { seasonStart } from "./MapScreen";

export function Coin({ id, half = false, size = 120, spin = true }: { id: SpeciesId; half?: boolean; size?: number; spin?: boolean }) {
  return (
    <motion.div className={"coin" + (half ? " half" : "")} style={{ width: size, height: size, padding: size * 0.07 }}
      initial={spin ? { rotateY: 720, scale: 0.2, y: -120 } : false} animate={{ rotateY: 0, scale: 1, y: 0 }} transition={{ duration: 1.1, ease: "easeOut" }}>
      <div style={{ width: "100%", height: "100%", borderRadius: "50%", overflow: "hidden", border: "2px solid #2A2A1C", position: "relative" }}>
        <img src={ART(`species_${id}`)} alt={sp(id).cn} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 14%", filter: half ? "grayscale(.7) contrast(.9)" : undefined }} />
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, background: "rgba(42,42,28,.82)", color: "#F3D27F", textAlign: "center", fontFamily: "var(--display)", fontSize: size * 0.17, padding: "2px 0 4px" }}>{sp(id).cn}</div>
      </div>
    </motion.div>
  );
}

export function Station({ onNext }: { onNext: () => void }) {
  const { g, update } = useGame();
  const rec = cur(g!);
  const scene = sceneById(rec.scene!)!;
  const { icons, why } = useMemo(() => iconsOf(rec), [rec.scene]);
  const { top, max } = topOf(icons);
  const tie = top.length !== 1;
  const [retest, setRetest] = useState<null | "tie" | "disagree">(null);
  const [card, setCard] = useState<RetestCard | null>(null);
  const [claim, setClaim] = useState<SpeciesId | null>(null);
  const [selfPick, setSelfPick] = useState(false);
  const [verdict, setVerdict] = useState<string | null>(null);
  const [minted, setMinted] = useState<SpeciesId | null>(rec.coin || (tie ? null : top[0]));
  const [changed, setChanged] = useState(!!rec.coinChanged);
  const [text, setText] = useState("");
  const half = !!rec.recognized;
  const quick = g!.mode === "quick";
  const last = quick || g!.seasonIdx >= 3;
  const entries = (Object.entries(icons) as [SpeciesId, number][]).sort((a, b) => b[1] - a[1]);

  function drawTie() {
    sfx.paper();
    setCard(retestFor(top.length ? "tie" : "none", top));
    setRetest("tie");
  }

  function pickClaim(s: SpeciesId) {
    sfx.paper();
    setClaim(s);
    setCard(retestFor("claim", [s]));
  }

  function answer(i: number) {
    const c = card!;
    let s = c.a[i].species;
    if (retest === "tie") {
      if (s === "other") {
        const rest = top.filter((t) => t !== "chameleon");
        if (top.includes("chameleon") && rest.length === 1) s = rest[0];
        else return setSelfPick(true);
      }
      sfx.coin();
      update((x) => void (cur(x).retest = { id: c.id, answer: i, species: s as SpeciesId, why: "tie" }));
      setMinted(s as SpeciesId);
      setRetest(null);
      return;
    }
    const ok = s === claim;
    update((x) => void (cur(x).retest = { id: c.id, answer: i, species: (ok ? claim : minted)!, why: "disagree", claim: claim! }));
    if (ok) {
      sfx.coin();
      setMinted(claim);
      setChanged(true);
      setVerdict(`答案支持你：换成${sp(claim!).cn}币，委托单上记一个“改”。`);
    } else {
      sfx.tap();
      setVerdict(`这个回答更像${s === "other" ? "别的物种" : sp(s as SpeciesId).cn}，没有支持你的主张：币不换。`);
    }
    setRetest(null);
  }

  function chooseSelf(s: SpeciesId) {
    sfx.coin();
    update((x) => void (cur(x).retest = { id: card!.id, answer: 1, species: s, why: "tie", selfPick: true }));
    setMinted(s);
    setSelfPick(false);
    setRetest(null);
  }

  function accept() {
    sfx.stamp();
    update((x) => {
      const r = cur(x);
      r.icons = icons;
      r.coin = minted!;
      r.coinHalf = half;
      r.coinChanged = changed;
      if (text) r.disagreeText = text;
      if (x.mode === "quick" || x.seasonIdx >= 3) {
        x.phase = "ending";
        x.finishedAt = Date.now();
      } else {
        x.seasonIdx += 1;
        x.pos = seasonStart(x.seasonIdx);
        x.rp += 1;
        x.seasons.push(newSeason(SEASONS[x.seasonIdx].id));
        x.phase = "map";
        x.step = "blind";
      }
    });
    onNext();
  }

  return (
    <div className={`screen s-${scene.season}`}>
      <Hud title="驿站" />
      <div className="pad">
        <div className="kicker">{quick ? "这一场结束 · 驿站" : `${scene.season_cn}季结束 · 驿站`}</div>
        <h2 className="h2 mt4">{quick ? "这一场，你像哪一种？" : "这一季，你像哪一种？"}</h2>
        <div className="stripe mt8" style={{ width: 80 }} />
        <p className="small muted mt8">你的每个做法都像一种动物。最像的那种，发一枚<Help k="物种币">物种币</Help>。</p>
        <div className="card mt12">
          <div className="tiny bold mb8">为什么说你像它</div>
          {why.length ? (
            <div className="col gap8">
              {why.map((w, i) => (
                <motion.div key={i} className="row gap8" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 + i * 0.2 }}>
                  <SpeciesAvatar id={w.species} size={30} />
                  <span className="small grow">因为{w.text}</span>
                  <b>×{w.n}</b>
                </motion.div>
              ))}
            </div>
          ) : <div className="small muted">这一季没有留下物种图标（理由是直觉或看不懂，也没看证据）。</div>}
          <div className="dash mt12 mb8" />
          <div className="row wrap gap6">
            {entries.map(([s, n]) => <span key={s} className={"pill" + (top.includes(s) ? " dark" : "")}>{sp(s).cn} {n}</span>)}
          </div>
        </div>
        <AnimatePresence mode="wait">
          {minted ? (
            <motion.div key={minted} className="center mt16" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <div style={{ display: "grid", placeItems: "center" }} onAnimationStart={() => sfx.coin()}><Coin id={minted} half={half} /></div>
              <div className="h3 mt12">{sp(minted).cn}币{half ? " · 半枚" : ""}{changed ? " · 改" : ""}</div>
              <div className="small muted mt4">{half ? "这一场你说认出来了：已经知道结局，这枚币只算半枚。" : tie && rec.retest?.selfPick ? "补测牌也没分出来：你自己挑的，档案上记“待确认”。" : tie && rec.retest ? "平局，按补测题的答案拿币。" : `最多的是${sp(minted).cn}（${max} 个图标）。`}</div>
              {verdict && <div className="small mt8 bold">{verdict}</div>}
              {!rec.retest && !tie && !verdict && (
                <>
                  <button className="btn ghost sm mt8" onClick={() => { setClaim(null); setCard(null); setRetest("disagree"); }}>我不同意，我觉得更像…</button>
                  <div className="tiny mt4">答一道补测题，答案支持你就换币</div>
                </>
              )}
            </motion.div>
          ) : (
            <motion.div key="tie" className="card mt16 center" style={{ background: "#FFF4D6" }}>
              <b className="h3">{top.length ? `${top.map((t) => sp(t).cn).join("和")}打平了` : "这一季没有图标"}</b>
              <div className="small mt4">{top.length ? "抽一张写着这两种物种的补测牌回答，按答案拿币，不能自己挑。" : "抽牌堆顶那张补测牌回答，按答案拿币。"}</div>
              <button className="btn season mt12" onClick={drawTie}>抽补测牌</button>
            </motion.div>
          )}
        </AnimatePresence>
        {minted && (
          <Fade delay={0.6}>
            <button className="btn season big block mt16" onClick={accept}>{quick ? "收下，去看初步画像 →" : last ? "收下，去终局：揭晓物种 →" : `收下，去${SEASONS[g!.seasonIdx + 1].cn} · ${SEASONS[g!.seasonIdx + 1].name} →`}</button>
          </Fade>
        )}
      </div>
      <Sheet open={!!retest} onClose={() => setRetest(null)} dismissable={retest === "disagree"}>
        <div className="kicker">补测牌{card?.pair && !card.pair.includes("other") ? ` · ${card.pair.map((s) => sp(s as SpeciesId).cn).join(" / ")}` : card ? " · 变色龙 / 任意" : ""}</div>
        {retest === "disagree" && !claim && (
          <div className="mt8">
            <div className="h3">你觉得这一季更像哪一种？</div>
            <div className="small muted mt4">抽一张写着这种物种的补测牌。答案支持你，就换币。</div>
            <div className="row wrap gap8 mt12">
              {PICKABLE.filter((s) => s.id !== minted).map((s) => (
                <button key={s.id} className="chip row gap6" style={{ padding: "6px 12px 6px 6px" }} onClick={() => pickClaim(s.id)}><SpeciesAvatar id={s.id} size={30} />{s.cn}</button>
              ))}
            </div>
          </div>
        )}
        {retest === "disagree" && claim && (
          <div className="mt8">
            <div className="small">说一句你为什么觉得自己更像{sp(claim).cn}（可选，只存在这台手机里）：</div>
            <input value={text} onChange={(e) => setText(e.target.value)} placeholder="比如：我其实是在等估值回落" style={{ width: "100%", marginTop: 6, padding: "10px 12px", border: "2px solid #2A2A1C", borderRadius: 10, fontSize: 15, background: "#fff" }} />
          </div>
        )}
        {card && !selfPick && (
          <>
            <div className="h3 mt12">{card.q}</div>
            <div className="col gap8 mt12">
              {card.a.map((a, i) => (
                <button key={i} className="opt" style={{ gridTemplateColumns: "38px 1fr" }} onClick={() => answer(i)}>
                  <span className="key">{"甲乙丙丁"[i]}</span><span>{a.text}</span>
                </button>
              ))}
            </div>
          </>
        )}
        {selfPick && (
          <div className="mt8">
            <div className="h3">补测牌也没分出来</div>
            <div className="small muted mt4">打平的{top.map((t) => sp(t).cn).join("和")}都不是变色龙：在里面自己挑一个，档案上记“待确认”。</div>
            <div className="row wrap gap8 mt12">
              {top.map((s) => (
                <button key={s} className="chip row gap6" style={{ padding: "6px 12px 6px 6px" }} onClick={() => chooseSelf(s)}><SpeciesAvatar id={s} size={30} />{sp(s).cn}</button>
              ))}
            </div>
          </div>
        )}
      </Sheet>
    </div>
  );
}
