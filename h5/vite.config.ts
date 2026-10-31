import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/ts/",
  plugins: [react()],
  build: {
    target: "es2019",
    assetsInlineLimit: 0,
    chunkSizeWarningLimit: 1600,
  },
});
