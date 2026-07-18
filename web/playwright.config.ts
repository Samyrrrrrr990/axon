import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 180_000,
  use: {
    viewport: { width: 1440, height: 900 },
  },
});
