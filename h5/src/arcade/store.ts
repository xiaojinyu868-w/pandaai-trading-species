import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Run } from "./Game";
import type { Verdict } from "./profile";

export type Stage = "cold" | "play" | "reveal" | "guess" | "judge" | "final";

interface Arcade {
  idx: number;
  stage: Stage;
  runs: Run[];
  lines: Record<string, string>;
  guess: string | null;
  verdict: Verdict | null;
  set: (p: Partial<Arcade>) => void;
  reset: () => void;
}

const FRESH = { idx: 0, stage: "cold" as Stage, runs: [] as Run[], lines: {}, guess: null, verdict: null };

export const useArcade = create<Arcade>()(
  persist(
    (set) => ({
      ...FRESH,
      set: (p) => set(p),
      reset: () => set({ ...FRESH }),
    }),
    { name: "ts-arcade-v1", partialize: ({ set: _s, reset: _r, ...rest }) => rest as Arcade },
  ),
);
