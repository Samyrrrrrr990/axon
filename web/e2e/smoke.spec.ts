import { expect, test } from "@playwright/test";

// Assumes the Axon server is running on :8700 with the built frontend.
const BASE = process.env.AXON_URL || "http://127.0.0.1:8700";

test("app loads, gallery opens, example runs", async ({ page }) => {
  await page.goto(BASE);
  await expect(page).toHaveTitle(/Axon/);

  // Open the gallery deterministically via the topbar (it may also auto-open on first run).
  const galleryHeading = page.getByText("Start from an example", { exact: true });
  await page.waitForLoadState("networkidle");
  if (!(await galleryHeading.isVisible().catch(() => false))) {
    await page.getByRole("button", { name: "Examples", exact: true }).click();
  }
  await expect(galleryHeading).toBeVisible();

  // Open the house-prices example → canvas shows its nodes.
  await page.getByText("Predict House Prices").click();
  const canvas = page.locator(".react-flow");
  await expect(canvas.getByText("Random Forest")).toBeVisible();
  await expect(canvas.getByText("Train / Test Split")).toBeVisible();

  // Run it and wait for success.
  await page.getByRole("button", { name: /Run/ }).click();
  await expect(page.getByText("finished", { exact: true })).toBeVisible({ timeout: 120_000 });
});
