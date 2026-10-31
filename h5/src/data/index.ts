import scenesJson from "./scenes.json";
import decksJson from "./decks.json";
import qrJson from "./qr.json";

export type SceneId = "s924" | "s2015" | "smt" | "scb" | "squant" | "soil";
export type SeasonId = "spring" | "summer" | "autumn" | "winter";
export type EvKind = "price" | "data" | "news" | "tip";
export type OptKey = "A" | "B" | "C" | "D";

export interface Chart {
  type?: "bars" | "line";
  values: number[];
  labels?: string[];
  unit?: string;
  t_index?: number;
  label?: string;
  dates?: string[];
  marks?: { i: number; date: string; label: string }[];
}
export interface Evidence {
  kind: EvKind;
  label: string;
  title: string;
  lines: string[];
  stat: { value: string; caption: string } | null;
  chart: Chart | null;
  risk: boolean;
  species: string | null;
  source: string;
}
export interface FFCard {
  title: string;
  lines: string[];
  per_share: number;
  pct: number;
  dropped: boolean;
  then: string;
  dip?: { date: string; pct_at_trigger: number; per_share_at_trigger: number; rest_pct: number; rest_per_share: number } | null;
  days?: { date: string; pct?: number; open_pct?: number; close_pct?: number }[];
  signal?: { ma5: number; ma20: number; red: boolean; first_cross_date: string };
  far?: { per_share: number; pct: number };
  us_pct?: number;
}
export interface Exit {
  name: string;
  url: string;
  why: string;
  kind: string;
  is_real: boolean;
  note?: string;
  prompt?: string;
  login?: boolean;
}
export interface PayoffRow { key: OptKey; label: string; shares: number; seg1: number; seg2: number; total: number }
export interface Day { date: string; open: number; high: number; low: number; close: number }
export interface Scene {
  id: SceneId;
  season: SeasonId;
  season_cn: string;
  season_name: string;
  door: "A" | "B";
  tier: string;
  title: string;
  year: string;
  market: string;
  door_hint: string;
  decision_mode: "sequential" | "simultaneous";
  t_date: string;
  t_text: string;
  path?: { instrument: string; t: number; ends: number[]; days: Day[] };
  blind: { headline: string; lines: string[]; position: string; question: string; chart: Chart };
  options: { key: OptKey; label: string; shares: number; hint?: string }[];
  evidence: Record<EvKind, Evidence>;
  fast_forward: {
    title: string;
    mechanic: string;
    mechanic_name: string;
    board_rules: string[];
    cards: FFCard[];
    holiday_ticker?: string[];
    grid?: { date: string; pct: number; note?: string; n?: number; limit_down?: number; suspended?: number; lock?: boolean }[];
    online_note?: string;
    second_decision?: { prompt: string; choices: { key: string; label: string; delta: number }[] };
    qr?: string;
  };
  reveal: {
    headline: string;
    date_line: string;
    lines: string[];
    lesson: string;
    egg?: string;
    rule_note?: string | null;
    chart: Chart;
    seg2: { label: string; pct: number; per_share: number };
    seg1_total?: { pct: number; per_share: number };
    payoff_rows: PayoffRow[];
    second_rows?: { key: string; label: string; seg2_extra: number | null; note: string }[];
    source_note: string;
  };
  exits: Exit[];
  qr: Record<string, string>;
}

export interface QrRow { id: string; code: string; url: string; route: string; printed_on: string; tier: string }

const S = scenesJson as unknown as { scenes: Scene[]; teasers: { id: string; title: string; season: string; door: string; note: string }[]; data_source: any; payoff_rule: string };
export const SCENES: Scene[] = S.scenes;
export const TEASERS = S.teasers || [];
export const DATA_SOURCE = S.data_source;
export const PAYOFF_RULE = S.payoff_rule;
export const sceneById = (id: string) => SCENES.find((s) => s.id === id);
export const DECKS: any = decksJson || {};
export const QR: QrRow[] = ((qrJson as any).codes || (Array.isArray(qrJson) ? qrJson : [])) as QrRow[];
export const qrById = (id: string) => QR.find((q) => q.id === id);

export const SEASONS: { id: SeasonId; cn: string; name: string; doors: SceneId[] }[] = [
  { id: "spring", cn: "春", name: "入场", doors: ["s924"] },
  { id: "summer", cn: "夏", name: "杠杆", doors: ["s2015"] },
  { id: "autumn", cn: "秋", name: "抱团", doors: ["smt", "squant"] },
  { id: "winter", cn: "冬", name: "危机", doors: ["scb", "soil"] },
];

export const ART = (name: string) => `${import.meta.env.BASE_URL}art/${name}.webp`;
