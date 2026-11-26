import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Geliştirmede `/api` istekleri backend'e (uvicorn, 8000) yönlendirilir.
// Tarayıcı açısından frontend ve API aynı adreste olur: çerez ve CORS sorunu çıkmaz (ADR-007).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});
