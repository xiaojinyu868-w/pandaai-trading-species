import { AnimatePresence, motion, animate, useMotionValue, useTransform } from "framer-motion";
import { useEffect, useState, type ReactNode } from "react";
import { ART } from "../data";
import { sp, type SpeciesId } from "../game/meta";
import { isMuted, setMuted, sfx } from "../lib/sound";

export function Sheet({ open, onClose, children, center = false, dismissable = true }: { open: boolean; onClose?: () => void; children: ReactNode; center?: boolean; dismissable?: boolean }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div className={"scrim" + (center ? " modal-center" : "")} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          onClick={() => dismissable && onClose?.()}>
          <motion.div className="sheet" onClick={(e) => e.stopPropagation()}
            initial={center ? { scale: 0.85, opacity: 0, rotate: -2 } : { y: "100%" }}
            animate={center ? { scale: 1, opacity: 1, rotate: 0 } : { y: 0 }}
            exit={center ? { scale: 0.9, opacity: 0 } : { y: "100%" }}
            transition={{ type: "spring", damping: 24, stiffness: 260 }}>
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export function Steps({ n, at, labels }: { n: number; at: number; labels?: string[] }) {
  return (
    <div>
      <div className="steps">
        {Array.from({ length: n }).map((_, i) => (
          <i key={i} className={i < at ? "on" : i === at ? "cur" : ""} />
        ))}
      </div>
      {labels && (
        <div className="steps-labels">
          {labels.map((l, i) => <span key={i} className={i < at ? "on" : i === at ? "cur" : ""}>{l}</span>)}
        </div>
      )}
    </div>
  );
}

export function RP({ n, max = 0, compact = false }: { n: number; max?: number; compact?: boolean }) {
  const total = Math.max(n, max);
  if (compact && total > 3) return <span className="row gap4"><i className="rp-dot" /><b>×{n}</b></span>;
  return (
    <span className="row gap4">
      {Array.from({ length: Math.min(total, 8) }).map((_, i) => (
        <motion.i key={i} className={"rp-dot" + (i < n ? "" : " off")} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: i * 0.04 }} />
      ))}
      {total > 8 && <b>+{total - 8}</b>}
    </span>
  );
}

/** 数字滚动 */
export function Counter({ value, className, prefix = "", signedMode = false }: { value: number; className?: string; prefix?: string; signedMode?: boolean }) {
  const mv = useMotionValue(value);
  const [shown, setShown] = useState(value);
  useEffect(() => {
    const c = animate(mv, value, { duration: 0.9, ease: "easeOut" });
    const un = mv.on("change", (v) => setShown(Math.round(v * 10) / 10));
    return () => {
      c.stop();
      un();
    };
  }, [value]);
  const d = Number.isInteger(value) ? 0 : 1;
  const a = Math.abs(shown).toFixed(d);
  const txt = signedMode ? (shown > 0 ? "+" : shown < 0 ? "−" : "±") + a : (shown < 0 ? "−" : "") + a;
  return <span className={className}>{prefix}{txt}</span>;
}

export function Stars({ n, max = 4, size = 22 }: { n: number; max?: number; size?: number }) {
  return (
    <span className="row gap4">
      {Array.from({ length: max }).map((_, i) => (
        <motion.svg key={i} width={size} height={size} viewBox="0 0 24 24" initial={{ scale: 0, rotate: -40 }} animate={{ scale: 1, rotate: 0 }}
          transition={{ delay: 0.15 + i * 0.18, type: "spring", stiffness: 300 }}>
          <path d="M12 2l2.9 6.6 7.1.6-5.4 4.7 1.6 7-6.2-3.7-6.2 3.7 1.6-7L2 9.2l7.1-.6z" fill={i < n ? "#C79A2E" : "none"} stroke="#2A2A1C" strokeWidth="1.8" strokeLinejoin="round" />
        </motion.svg>
      ))}
    </span>
  );
}

export function SpeciesAvatar({ id, size = 44, ring = true }: { id: SpeciesId | string; size?: number; ring?: boolean }) {
  const s = sp(id);
  return (
    <span style={{ width: size, height: size, borderRadius: "50%", overflow: "hidden", display: "inline-block", border: ring ? "2px solid #2A2A1C" : "none", background: s?.color || "#ccc", flex: "none" }}>
      <img src={ART(`species_${id}`)} alt={s?.cn} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 18%" }} />
    </span>
  );
}

export function Glyph({ ch, color = "#2A2A1C", size = 40, filled = true }: { ch: string; color?: string; size?: number; filled?: boolean }) {
  return (
    <span style={{ width: size, height: size, borderRadius: "50%", display: "inline-grid", placeItems: "center", border: "2px solid #2A2A1C", background: filled ? color : "transparent", color: filled ? "#FBF4E4" : color, fontFamily: "var(--display)", fontSize: size * 0.5, flex: "none" }}>
      {ch}
    </span>
  );
}

export function MuteButton() {
  const [m, setM] = useState(isMuted());
  return (
    <button className="btn ghost sm" style={{ padding: "6px 10px" }} onClick={() => { setMuted(!m); setM(!m); if (m) sfx.tap(); }} aria-label="声音">
      {m ? "🔇" : "🔊"}
    </button>
  );
}

export function Typing({ text, speed = 28, onDone, className }: { text: string; speed?: number; onDone?: () => void; className?: string }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    setN(0);
    const id = setInterval(() => setN((x) => {
      if (x >= text.length) {
        clearInterval(id);
        onDone?.();
        return x;
      }
      return x + 1;
    }), speed);
    return () => clearInterval(id);
  }, [text]);
  return <span className={className}>{text.slice(0, n)}<span style={{ opacity: n < text.length ? 1 : 0 }} className="blink">▌</span></span>;
}

export function Money({ n, big = false, u = "" }: { n: number; big?: boolean; u?: string }) {
  return <span className={(n > 0 ? "up" : n < 0 ? "down" : "") + (big ? " delta" : " bold")}>{n > 0 ? "+" : n < 0 ? "−" : "±"}{Math.abs(n)}{u && <small style={{ fontSize: "0.6em", marginLeft: 1 }}>{u}</small>}</span>;
}

export function Pct({ p, d = 1 }: { p: number; d?: number }) {
  return <span className={p > 0 ? "up" : p < 0 ? "down" : ""}>{p > 0 ? "+" : p < 0 ? "−" : ""}{Math.abs(p).toFixed(d)}%</span>;
}

export function ExampleTag({ children = "示例" }: { children?: ReactNode }) {
  return <span className="pill example">{children}</span>;
}

export function Fade({ children, delay = 0, y = 14 }: { children: ReactNode; delay?: number; y?: number }) {
  return <motion.div initial={{ opacity: 0, y }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.45, ease: "easeOut" }}>{children}</motion.div>;
}

export function useTimer(ms: number, deps: any[] = []) {
  const [done, setDone] = useState(false);
  useEffect(() => {
    setDone(false);
    const t = setTimeout(() => setDone(true), ms);
    return () => clearTimeout(t);
  }, deps);
  return done;
}

export const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export function Shares({ n, max = 3 }: { n: number; max?: number }) {
  return (
    <span className="shares">
      {Array.from({ length: Math.max(max, n) }).map((_, i) => <i key={i} className={i < n ? "f" : ""} />)}
    </span>
  );
}

export function useMotionNumber(v: number) {
  const mv = useMotionValue(v);
  const r = useTransform(mv, (x) => Math.round(x));
  useEffect(() => {
    const c = animate(mv, v, { duration: 0.8 });
    return () => c.stop();
  }, [v]);
  return r;
}
