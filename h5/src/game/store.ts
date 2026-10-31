import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { EvKind, OptKey, SceneId, SeasonId } from "../data";
import type { Plan, Reason, SpeciesId } from "./meta";
import type { Run } from "../arcade/Game";
import type { Verdict } from "../arcade/profile";

export type TileKind = "supply" | "chance" | "research" | "dataport" | "calm" | "door";
export type Phase = "home" | "prologue" | "self" | "map" | "pick" | "scene" | "station" | "ending";
export type SceneStep = "blind" | "evidence" | "slip" | "flip" | "ff" | "reveal";

export interface AiResult { option: OptKey; seg1: number; seg2: number; extra: number; total: number; line: string; ff: string; stars: number }

export interface SeasonRec {
  season: SeasonId;
  dice?: [number, number];
  picked?: number;
  tile?: TileKind;
  rerolled?: boolean;
  chance?: { id: string; answer: number; species: SpeciesId };
  rulesOffered?: string[];
  ruleKept?: string;
  dataport?: { id: string; answer: number; correct: boolean } | "skip";
  calm?: "sat" | "skip";
  freeEvidence?: number;
  rpGained: number;
  scene?: SceneId;
  door?: "A" | "B";
  recognized?: { name: string; correct: boolean } | null;
  evidence: EvKind[];
  evidenceMs: Partial<Record<EvKind, number>>;
  option?: OptKey;
  reason?: Reason;
  ruleId?: string;
  plan?: Plan;
  queueSeen?: number;
  ff?: {
    actions: string[];
    changes: number;
    planTriggered: boolean;
    planFollowed: boolean | null;
    ruleFollowed: boolean | null;
    second?: string;
    sellDay?: string;
    locked?: number;
    forced?: boolean;
    leavers?: number;
    debt?: boolean;
  };
  money?: { seg1: number; seg2: number; extra: number; total: number; counted: number; note?: string };
  stars?: { ev: number; consistent: boolean; plan: boolean; total: number };
  icons?: Partial<Record<SpeciesId, number>>;
  coin?: SpeciesId;
  coinHalf?: boolean;
  coinChanged?: boolean;
  retest?: { id: string; answer: number; species: SpeciesId; why: "tie" | "disagree"; selfPick?: boolean; claim?: SpeciesId };
  disagreeText?: string;
  ai?: Record<string, AiResult>;
  /** 线上名场面：小游戏里手上的真实操作，和 AI 的一句旁白 */
  run?: Run;
  line?: string;
}

export interface Game {
  id: string;
  phase: Phase;
  step: SceneStep;
  seasonIdx: number;
  pos: number;
  money: number;
  rp: number;
  self?: SpeciesId;
  opponents: string[];
  aiMoney: Record<string, number>;
  rules: string[];
  dataportRight: number;
  dataportSeen: number;
  seasons: SeasonRec[];
  real?: { drop?: string; buy?: string };
  /** 点开过解释的金融术语（按第一次点开的顺序） */
  terms?: string[];
  /** 点开游戏规则说明的次数 */
  helps?: number;
  mode?: "full" | "quick";
  /** 终局 AI 复盘结果（只用名场面小游戏里的操作） */
  verdict?: Verdict;
  startedAt: number;
  finishedAt?: number;
  source: "h5" | "record";
}

export const newSeason = (season: SeasonId): SeasonRec => ({ season, evidence: [], evidenceMs: {}, rpGained: 0 });

export function freshGame(): Game {
  return {
    id: Math.random().toString(36).slice(2, 10),
    phase: "prologue",
    step: "blind",
    seasonIdx: 0,
    pos: 0,
    money: 20,
    rp: 1,
    opponents: ["cheetah", "meerkat"],
    aiMoney: { cheetah: 20, meerkat: 20 },
    rules: [],
    dataportRight: 0,
    dataportSeen: 0,
    seasons: [newSeason("spring")],
    startedAt: Date.now(),
    source: "h5",
  };
}

interface Store {
  g: Game | null;
  muted: boolean;
  start: () => void;
  startQuick: () => void;
  reset: () => void;
  update: (fn: (g: Game) => void) => void;
  setMuted: (m: boolean) => void;
}

export const useGame = create<Store>()(
  persist(
    (set) => ({
      g: null,
      muted: false,
      start: () => set({ g: freshGame() }),
      startQuick: () => set({ g: { ...freshGame(), mode: "quick", phase: "self", rp: 2 } }),
      reset: () => set({ g: null }),
      update: (fn) =>
        set((s) => {
          if (!s.g) return s;
          const g: Game = JSON.parse(JSON.stringify(s.g));
          fn(g);
          return { g };
        }),
      setMuted: (m) => set({ muted: m }),
    }),
    { name: "ts-game-v1" },
  ),
);

export const cur = (g: Game) => g.seasons[g.seasonIdx];
