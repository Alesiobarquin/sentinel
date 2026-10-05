import { expect, test } from "@playwright/test";

test("landing page leads to the investigation and explanatory project", async ({
  page,
}) => {
  await page.goto("/sentinel/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Sentinel");
  await page.getByRole("link", { name: "View demo", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Payment investigation" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "The project", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Project notes",
  );
  await expect(
    page.getByRole("link", { name: "The project", exact: true }),
  ).toHaveAttribute("aria-current", "page");
});

test("step controls show the original metric read and reset coherently", async ({
  page,
}) => {
  await page.goto("/sentinel/demo/");
  await expect(
    page.getByRole("heading", { name: "Service inventory", level: 2 }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Next step", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Payment metrics", level: 2 }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Selected evidence" }),
  ).toContainText("9.00");
  await expect(
    page.getByRole("region", { name: "Selected evidence" }),
  ).toContainText("3 minimum raw counter samples");
  await page
    .getByText("Inspect the fixed Prometheus query", { exact: true })
    .click();
  await expect(
    page
      .locator("pre")
      .filter({ hasText: "increase(traces_span_metrics_calls_total" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Reset replay" }).click();
  await expect(
    page.getByRole("heading", { name: "Service inventory", level: 2 }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Previous step", exact: true }),
  ).toBeDisabled();
});

test("a diagnosis citation opens the actual global flag evidence", async ({
  page,
}) => {
  await page.goto("/sentinel/demo/");
  await page.getByRole("button", { name: "Jump to diagnosis" }).click();
  await expect(
    page.getByRole("heading", {
      name: "The paymentFailure fault branch is active.",
    }),
  ).toBeVisible();
  await page
    .locator(".diagnosis-panel")
    .getByRole("button", { name: "Inspect evidence ev_006" })
    .click();
  const panel = page.getByRole("region", { name: "Selected evidence" });
  await expect(panel).toContainText("paymentFailure");
  await expect(panel).toContainText("100%");
  await expect(panel).toContainText("not established by this read");
  await panel.getByText("Tool arguments & provenance", { exact: true }).click();
  await expect(panel.locator("pre")).toContainText('"service": null');
  await expect(panel.locator("pre")).toContainText('"period": null');
});

test("a deep replay link exposes trace sample limits and selected errors", async ({
  page,
}) => {
  await page.goto("/sentinel/demo/#step-3");
  await expect(
    page.getByRole("heading", { name: "Distributed traces", level: 2 }),
  ).toBeVisible();
  const panel = page.getByRole("region", { name: "Selected evidence" });
  await expect(panel).toContainText("6 traces returned · 3 selected");
  await expect(panel).toContainText("Read limit reached");
  await expect(panel).toContainText("77 spans omitted");
  await expect(panel).toContainText("Invalid token");
  await expect(panel).toContainText(
    "3 traces omitted from selected model context",
  );
});

test("source evidence identifies the pinned external application", async ({
  page,
}) => {
  await page.goto("/sentinel/demo/#step-4");
  const panel = page.getByRole("region", { name: "Selected evidence" });
  await expect(
    panel.getByRole("link", { name: "src/payment/charge.js" }),
  ).toHaveAttribute(
    "href",
    /open-telemetry\/opentelemetry-demo\/blob\/dedc0178918e/,
  );
  await expect(panel).toContainText("Math.random() < numberVariant");
  await panel
    .getByText("Full selected excerpt · 116/116 lines", { exact: true })
    .click();
  await expect(panel).toContainText("Copyright The OpenTelemetry Authors");
});

test("recovery clearly distinguishes the helper from agent remediation", async ({
  page,
}) => {
  await page.goto("/sentinel/demo/#step-9");
  await expect(
    page.getByRole("heading", { name: "Recovery checks" }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Current investigation step" }),
  ).toContainText("Sentinel did not execute remediation");
  await expect(
    page.getByRole("region", { name: "Current investigation step" }),
  ).toContainText("5/5");
  await expect(
    page.getByRole("button", { name: "Next step", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Previous step", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Diagnosis", level: 2 }),
  ).toBeVisible();
});

test("play and pause control condensed playback without changing recorded measurements", async ({
  page,
}) => {
  await page.clock.install();
  await page.goto("/sentinel/demo/");
  await page.getByRole("button", { name: "Play replay", exact: true }).click();
  await page.clock.fastForward(4000);
  await expect(
    page.getByRole("heading", { name: "Payment metrics", level: 2 }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Pause replay", exact: true }).click();
  await page.clock.fastForward(8000);
  await expect(
    page.getByRole("heading", { name: "Payment metrics", level: 2 }),
  ).toBeVisible();
  await expect(page.locator(".demo-stats")).toContainText("48,380 / 50,000");
});

test("architecture details and current limitations are inspectable", async ({
  page,
}) => {
  await page.goto("/sentinel/project/");
  await page.getByRole("button", { name: /Full local audit/ }).click();
  await expect(page.locator(".arch-detail")).toContainText(
    "PostgreSQL is not implemented",
  );
  await page.getByRole("link", { name: "Limits", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Current limitations" }),
  ).toBeVisible();
  await expect(page.locator("#limits")).toContainText(
    "complete delivery to Jaeger is unverified",
  );
});

test("public pages do not overflow or require external execution", async ({
  page,
}) => {
  const requests: string[] = [];
  const errors: string[] = [];
  page.on("request", (request) => requests.push(request.url()));
  page.on("pageerror", (error) => errors.push(error.message));
  for (const path of [
    "/sentinel/",
    "/sentinel/project/",
    "/sentinel/demo/#step-8",
  ]) {
    await page.goto(path);
    await expect(page.locator("h1")).toBeVisible();
    if (path.includes("demo"))
      await expect(page.locator(".diagnosis-panel")).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  }
  expect(errors).toEqual([]);
  const expectedHost = new URL(page.url()).host;
  expect(requests.every((url) => new URL(url).host === expectedHost)).toBe(
    true,
  );
});

test("the downloadable public record resolves under the repository path", async ({
  page,
  request,
}) => {
  await page.goto("/sentinel/demo/");
  const link = page.getByRole("link", { name: "Download public record" });
  await expect(link).toHaveAttribute("href", "/sentinel/investigation.json");
  const response = await request.get("/sentinel/investigation.json");
  expect(response.ok()).toBe(true);
  const payload = await response.json();
  expect(payload.run_id).toBe("b4e5c4bc-ad01-4fde-b147-6446762705e2");
  expect(payload.diagnosis.remediation_executed).toBe(false);
  expect(payload.evidence).toHaveLength(8);
  expect(JSON.stringify(payload)).not.toContain("server.address");
});

test("missing routes provide a useful return path", async ({ page }) => {
  const response = await page.goto("/sentinel/unknown/");
  expect(response?.status()).toBe(404);
  await expect(
    page.getByRole("heading", { name: "Page not found" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "View demo", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Payment investigation" }),
  ).toBeVisible();
});
