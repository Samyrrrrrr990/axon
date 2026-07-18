import { expect, test } from "@playwright/test";

const BASE = process.env.AXON_URL || "http://127.0.0.1:8700";

test("capture README screenshot", async ({ page }) => {
  await page.goto(BASE);
  await page.waitForLoadState("networkidle");

  const galleryHeading = page.getByText("Start from an example", { exact: true });
  if (!(await galleryHeading.isVisible().catch(() => false))) {
    await page.getByRole("button", { name: "Examples", exact: true }).click();
  }
  await page.getByText("Predict House Prices").click();

  await page.getByRole("button", { name: /Run/ }).click();
  await expect(page.getByText("finished", { exact: true })).toBeVisible({ timeout: 120_000 });

  // Select the evaluate node so the inspector shows metrics.
  await page.locator(".react-flow").getByText("Evaluate", { exact: true }).click();
  await page.getByRole("button", { name: "Output" }).click();
  await page.waitForTimeout(600);

  await page.screenshot({ path: "../docs/assets/canvas.png" });
});
