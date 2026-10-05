import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 25_000,
  reporter: "list",
  use: {
    baseURL: process.env.SITE_TEST_URL || "http://127.0.0.1:4173",
    browserName: "chromium",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { viewport: { width: 1440, height: 1000 } } },
    {
      name: "mobile",
      use: {
        viewport: { width: 390, height: 844 },
        isMobile: true,
        hasTouch: true,
      },
    },
  ],
  webServer: process.env.SITE_TEST_URL
    ? undefined
    : {
        command: "python3 ../../scripts/serve_site.py --port 4173",
        url: "http://127.0.0.1:4173/sentinel/",
        reuseExistingServer: !process.env.CI,
        timeout: 15_000,
      },
});
