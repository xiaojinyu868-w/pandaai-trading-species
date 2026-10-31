import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/ts/",
  plugins: [react()],
  server: { proxy: { "/ts-api": "http://127.0.0.1:8796" } },
  preview: { proxy: { "/ts-api": "http://127.0.0.1:8796" } },
  build: {
    target: "es2019",
    assetsInlineLimit: 0,
    chunkSizeWarningLimit: 1600,
  },
});
