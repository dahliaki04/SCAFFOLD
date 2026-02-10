import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "saas"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["tests/saas/**/*.test.{ts,tsx}"],
    setupFiles: ["tests/saas/setup.ts"],
  },
});
