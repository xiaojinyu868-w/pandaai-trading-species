import type { Scene } from "../data";

/** 每个名场面主走势用的数据：来源、标的、接口。盲测阶段只露来源和口径，不露标的名字。 */
const MAIN: Record<string, { src: "Panda Data" | "公开接口"; name: string; code: string; api?: string; field: string }> = {
  s924: { src: "Panda Data", name: "上证指数", code: "000001.SH", api: "get_index_daily", field: "日线收盘价" },
  s2015: { src: "Panda Data", name: "上证指数", code: "000001.SH", api: "get_index_daily", field: "日线收盘价" },
  smt: { src: "Panda Data", name: "贵州茅台（前复权）", code: "600519.SH", api: "get_stock_daily_pre", field: "日线收盘价" },
  squant: { src: "Panda Data", name: "国证 2000", code: "399303.SZ", api: "get_index_daily", field: "日线收盘价" },
  scb: { src: "公开接口", name: "纳斯达克 100", code: "NDX", field: "日线收盘价（腾讯证券）" },
  soil: { src: "公开接口", name: "WTI 原油连续合约", code: "CL", field: "日线结算价（新浪财经）" },
};

export const mainData = (id: string) => MAIN[id];

export function DataStamp({ scene, phase, dark = false }: { scene: Scene; phase: "blind" | "reveal"; dark?: boolean }) {
  const m = MAIN[scene.id];
  if (!m) return null;
  const isPanda = m.src === "Panda Data";
  if (phase === "blind") {
    return (
      <span className={"data-stamp" + (dark ? " dark" : "")}>
        <b>{isPanda ? "Panda Data" : "公开行情"}</b>
        <span>真实{m.field.replace(/（.*）/, "")} · 只显示你做决定那天之前的走势</span>
      </span>
    );
  }
  const dates = scene.reveal.chart.dates;
  return (
    <span className={"data-stamp" + (dark ? " dark" : "")}>
      <b>{isPanda ? "Panda Data" : "公开行情"}</b>
      <span>{m.name} {m.code}{m.api ? ` · ${m.api}` : ""} · {m.field}{dates ? ` · ${dates[0]} → ${dates[dates.length - 1]}` : ""} · 决定日 {scene.t_date}</span>
    </span>
  );
}

/** 证据卡底部的来源：含 Panda Data 的高亮 */
export function SourceLine({ text, dark = false }: { text: string; dark?: boolean }) {
  if (!text) return null;
  const panda = /Panda Data/.test(text);
  return (
    <div className="mt8">
      <span className={"data-stamp" + (dark ? " dark" : "")}>
        {panda && <b>Panda Data</b>}
        <span>{panda ? text.replace(/Panda Data\s*/g, "") : text}</span>
      </span>
    </div>
  );
}
