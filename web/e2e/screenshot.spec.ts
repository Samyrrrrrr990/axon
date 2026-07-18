import { expect, test } from "@playwright/test";

const BASE = process.env.AXON_URL || "http://127.0.0.1:8700";

async function openExample(page, title: string) {
  await page.goto(BASE);
  await page.waitForLoadState("networkidle");
  const galleryHeading = page.getByText("Start from an example", { exact: true });
  if (!(await galleryHeading.isVisible().catch(() => false))) {
    await page.getByRole("button", { name: "Examples", exact: true }).click();
  }
  await page.getByText(title).click();
  await page.waitForTimeout(400);
}

test("shot: gallery", async ({ page }) => {
  await page.goto(BASE);
  await page.waitForLoadState("networkidle");
  const galleryHeading = page.getByText("Start from an example", { exact: true });
  if (!(await galleryHeading.isVisible().catch(() => false))) {
    await page.getByRole("button", { name: "Examples", exact: true }).click();
  }
  await expect(galleryHeading).toBeVisible();
  await page.waitForTimeout(500);
  await page.screenshot({ path: "../docs/assets/gallery.png" });
});

test("shot: canvas with run and metrics", async ({ page }) => {
  await openExample(page, "Predict House Prices");
  await page.getByRole("button", { name: /Run/ }).click();
  await expect(page.getByText("finished", { exact: true })).toBeVisible({ timeout: 180_000 });
  await page.locator(".react-flow").getByText("Evaluate", { exact: true }).click();
  await page.getByRole("button", { name: "Output" }).click();
  await page.waitForTimeout(700);
  await page.screenshot({ path: "../docs/assets/canvas.png" });
});

test("shot: digits with confusion matrix", async ({ page }) => {
  await openExample(page, "Handwritten Digit Classifier");
  await page.getByRole("button", { name: /Run/ }).click();
  await expect(page.getByText("finished", { exact: true })).toBeVisible({ timeout: 300_000 });
  await page.locator(".react-flow").getByText("Confusion Matrix", { exact: true }).click();
  await page.getByRole("button", { name: "Output" }).click();
  await page.waitForTimeout(700);
  await page.screenshot({ path: "../docs/assets/confusion.png" });
});

test("shot: copilot sidebar", async ({ page }) => {
  await openExample(page, "Predict House Prices");
  await page.getByRole("button", { name: "Copilot" }).click();
  await page.waitForTimeout(600);
  await page.screenshot({ path: "../docs/assets/copilot.png" });
});
