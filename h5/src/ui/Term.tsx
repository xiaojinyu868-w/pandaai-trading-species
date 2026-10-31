import { motion } from "framer-motion";
import { Fragment, type ReactNode } from "react";
import { create } from "zustand";
import { GAME_TERMS, splitTerms, TERMS } from "../game/glossary";
import { useGame } from "../game/store";
import { sfx } from "../lib/sound";
import { Sheet } from "./kit";

interface TermUI { k: string | null; game: boolean; open: (k: string, game?: boolean) => void; close: () => void }
const useTermUI = create<TermUI>((set) => ({
  k: null,
  game: false,
  open: (k, game = false) => set({ k, game }),
  close: () => set({ k: null }),
}));

export function openTerm(k: string, game = false) {
  sfx.tap();
  useTermUI.getState().open(k, game);
  const { g, update } = useGame.getState();
  if (!g || g.phase === "ending" || g.source !== "h5") return;
  update((x) => {
    if (game) x.helps = (x.helps || 0) + 1;
    else if (!(x.terms || []).includes(k)) x.terms = [...(x.terms || []), k];
  });
}

/** 正文里的术语：虚线下划线，点开看解释。放在按钮里也能点，不会触发按钮本身。 */
export function Rich({ text, max = 4 }: { text: string; max?: number }) {
  const parts = splitTerms(text, new Set(), max);
  return (
    <>
      {parts.map((p, i) =>
        p.term ? (
          <span key={i} role="button" className="term"
            onClick={(e) => { e.stopPropagation(); e.preventDefault(); openTerm(p.term!); }}>{p.s}</span>
        ) : <Fragment key={i}>{p.s}</Fragment>,
      )}
    </>
  );
}

/** 游戏概念旁的小问号 */
export function Help({ k, children, light = false }: { k: keyof typeof GAME_TERMS | string; children?: ReactNode; light?: boolean }) {
  return (
    <span role="button" className={"help" + (light ? " light" : "")}
      onClick={(e) => { e.stopPropagation(); e.preventDefault(); openTerm(String(k), true); }}>
      {children}<i>?</i>
    </span>
  );
}

export function TermHost() {
  const { k, game, close } = useTermUI();
  const def = k ? (game ? GAME_TERMS[k] : TERMS[k]) : null;
  return (
    <Sheet open={!!def} onClose={close}>
      {def && (
        <motion.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
          <div className="kicker">{game ? "游戏规则" : "一句话解释"}</div>
          <div className="h2 mt4">{def.t}</div>
          <div className="stripe mt8" style={{ width: 64 }} />
          <p className="lead mt12" style={{ marginBottom: 0 }}>{def.d}</p>
          {"more" in def && def.more && <p className="body muted mt8" style={{ marginBottom: 0 }}>{def.more}</p>}
          <button className="btn block mt16" onClick={close}>知道了</button>
        </motion.div>
      )}
    </Sheet>
  );
}
