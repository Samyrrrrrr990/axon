import { test } from "@playwright/test";

const BASE = "http://127.0.0.1:8899";
const OUT = process.env.LAND_OUT || "/tmp";

test.skip(!process.env.LAND_OUT, "landing screenshots run only when LAND_OUT is set");

test("landing screenshots", async ({ browser }) => {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(BASE, { waitUntil: "networkidle" });
  await page.waitForTimeout(900);
  await page.screenshot({ path: `${OUT}/land-hero.png` });
  // Scroll through the page like a person so every reveal fires, then capture.
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 500) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 120));
    }
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(700);
  await page.screenshot({ path: `${OUT}/land-full.png`, fullPage: true });

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mobile.goto(BASE, { waitUntil: "networkidle" });
  await mobile.waitForTimeout(700);
  await mobile.screenshot({ path: `${OUT}/land-mobile.png` });
});
