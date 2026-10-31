import { motion } from "framer-motion";
import type { Chart as C } from "../data";

const W = 340;

const textW = (s: string) => [...s].reduce((a, c) => a + (c.charCodeAt(0) > 0x2e80 ? 10 : 6), 0);

/** 标记文字挨得太近时往下错一行 */
function placeTags(items: { cx: number; w: number }[]) {
  const ends: number[] = [];
  const at: { cx: number; row: number }[] = [];
  items
    .map((t, k) => ({ ...t, k }))
    .sort((a, b) => a.cx - b.cx)
    .forEach((t) => {
      const cx = Math.min(W - t.w / 2 - 2, Math.max(t.w / 2 + 2, t.cx));
      let row = ends.findIndex((e) => e + 4 <= cx - t.w / 2);
      if (row < 0) row = ends.push(0) - 1;
      ends[row] = cx + t.w / 2;
      at[t.k] = { cx, row };
    });
  return { at, rows: Math.max(1, ends.length) };
}

/** 折线：从左往右画出来；highlight 之后的部分用季节色 */
export function LineChart({ values, height = 150, marks = [], color = "#2A2A1C", fill = true, base, cut, animateDraw = true, labels, endDot = true }: {
  values: number[]; height?: number; marks?: { i: number; label: string }[]; color?: string; fill?: boolean; base?: number; cut?: number; animateDraw?: boolean; labels?: [string, string]; endDot?: boolean;
}) {
  if (!values?.length) return null;
  const pad = 8;
  const n = values.length;
  const shown = cut != null ? values.slice(0, cut + 1) : values;
  const lo = Math.min(...values, base ?? Infinity);
  const hi = Math.max(...values, base ?? -Infinity);
  const x = (i: number) => pad + (i / (n - 1)) * (W - pad * 2);
  const tags = placeTags(marks.map((m) => ({ cx: x(m.i), w: textW(m.label) })));
  const top = marks.length ? 14 + (tags.rows - 1) * 12 : 0;
  const y = (v: number) => pad + (1 - (v - lo) / (hi - lo || 1)) * (height - pad * 2 - top) + top;
  const d = shown.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area = `${d} L${x(shown.length - 1).toFixed(1)},${height - pad} L${x(0).toFixed(1)},${height - pad} Z`;
  const last = shown[shown.length - 1];
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${height}`} preserveAspectRatio="none" style={{ overflow: "visible" }}>
      {base != null && <line x1={pad} x2={W - pad} y1={y(base)} y2={y(base)} stroke="#77745A" strokeDasharray="3 4" strokeWidth="1" />}
      {fill && <motion.path d={area} fill={color} opacity={0.1} initial={{ opacity: 0 }} animate={{ opacity: 0.1 }} transition={{ delay: animateDraw ? 1 : 0 }} />}
      <motion.path d={d} fill="none" stroke={color} strokeWidth="2.6" strokeLinejoin="round" strokeLinecap="round"
        initial={animateDraw ? { pathLength: 0 } : false} animate={{ pathLength: 1 }} transition={{ duration: 1.4, ease: "easeInOut" }} />
      {marks.map((m, k) => (
        <g key={k}>
          <line x1={x(m.i)} x2={x(m.i)} y1={13 + tags.at[k].row * 12} y2={height - pad} stroke="#C79A2E" strokeWidth="1.5" strokeDasharray="2 3" />
          <text x={tags.at[k].cx} y={10 + tags.at[k].row * 12} fontSize="10" fontWeight="700" fill="#4A4A33" textAnchor="middle">{m.label}</text>
        </g>
      ))}
      {endDot && <motion.circle cx={x(shown.length - 1)} cy={y(last)} r={4.5} fill="#D4432A" stroke="#2A2A1C" strokeWidth="1.5" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: animateDraw ? 1.4 : 0 }} />}
      {labels && (
        <>
          <text x={pad} y={height + 12} fontSize="10" fill="#77745A">{labels[0]}</text>
          <text x={W - pad} y={height + 12} fontSize="10" fill="#77745A" textAnchor="end">{labels[1]}</text>
        </>
      )}
    </svg>
  );
}

/** 柱状：涨红跌绿；有正负时以 0 为轴 */
export function Bars({ values, height = 110, highlightLast = true, unit, labels, neutral = false }: { values: number[]; height?: number; highlightLast?: boolean; unit?: string; labels?: string[]; neutral?: boolean }) {
  if (!values?.length) return null;
  const pad = 4;
  const n = values.length;
  const neg = values.some((v) => v < 0);
  const hi = Math.max(...values, 0);
  const lo = Math.min(...values, 0);
  const bw = (W - pad * 2) / n;
  const y = (v: number) => pad + (1 - (v - lo) / (hi - lo || 1)) * (height - pad * 2);
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${height}`} preserveAspectRatio="none">
      {neg && <line x1={0} x2={W} y1={y(0)} y2={y(0)} stroke="#2A2A1C" strokeWidth="1" />}
      {values.map((v, i) => {
        const top = Math.min(y(v), y(0));
        const h = Math.max(1.5, Math.abs(y(v) - y(0)));
        const last = highlightLast && i === n - 1;
        const col = neutral ? (last ? "#D4432A" : "#77745A") : v >= 0 ? "#D4432A" : "#3C7A4E";
        return (
          <motion.rect key={i} x={pad + i * bw + bw * 0.12} width={bw * 0.76} y={top} height={h} rx={1.5}
            fill={col} opacity={last || !highlightLast ? 1 : 0.55} stroke={last ? "#2A2A1C" : "none"} strokeWidth={1.2}
            initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} style={{ originY: neg ? `${y(0)}px` : `${height}px`, transformBox: "view-box" as any }}
            transition={{ delay: i * (0.6 / n), duration: 0.35 }} />
        );
      })}
    </svg>
  );
}

export function EvChart({ c }: { c: C | null | undefined }) {
  if (!c) return null;
  return (
    <div>
      {c.type === "bars" ? <Bars values={c.values} neutral={!c.values.some((v) => v < 0)} /> : <LineChart values={c.values} height={120} labels={c.labels?.length === 2 ? [c.labels[0], c.labels[1]] : undefined} />}
      {c.unit && <div className="chart-cap" style={{ marginTop: c.type === "bars" ? 2 : 14 }}>{c.unit}</div>}
    </div>
  );
}
