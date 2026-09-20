// Optional browser regression check. Requires Playwright and a running local site.
const { chromium, expect } = require('playwright/test');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');

const baseURL = process.env.VESSELS_BASE_URL || 'http://127.0.0.1:5053';
const data = JSON.parse(readFileSync(resolve(__dirname, '../wwwroot/data/vessels/unloading.json'), 'utf8'));
const engineeringData = JSON.parse(readFileSync(resolve(__dirname, '../wwwroot/data/vessels/engineering.json'), 'utf8'));
const totalVesselCount = data.vessels.length + engineeringData.vessels.length;
const collator = new Intl.Collator('nb-NO', { sensitivity: 'base' });

async function checkOrder(page, section) {
    const names = await page.locator(`.vessel-section--${section} .vessel-name`).allTextContents();
    const sorted = [...names].sort(collator.compare);
    expect(names).toEqual(sorted);
}

async function main() {
    const browser = await chromium.launch({
        headless: true,
        ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE
            ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {}),
    });
    try {
        const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
        // Browser checks exercise our site without sending analytics or loading external pages.
        await context.route(/https:\/\/(static\.cloudflareinsights\.com|cloudflareinsights\.com)\//,
            route => route.fulfill({ status: 200, contentType: 'text/javascript', body: '' }));
        const errors = [];
        context.on('page', page => page.on('pageerror', error => errors.push(error.message)));
        const page = await context.newPage();
        await page.goto(`${baseURL}/vessels`);
        const boats = page.locator('.vessel-toggle');
        const info = page.getByRole('switch');
        const sort = page.getByRole('button', { name: /Sorter begge båtlister/ });
        const list = page.locator('.vessel-section--unloading .vessel-list');
        const totalBadge = page.locator('.vessel-total');
        const totalTonnes = data.vessels.flatMap(vessel => vessel.entries)
            .filter(entry => entry.includeInTotal && entry.tonnes !== null)
            .reduce((total, entry) => total + entry.tonnes, 0);
        const totalLabel = new Intl.NumberFormat('nb-NO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(totalTonnes);
        await expect(boats).toHaveCount(totalVesselCount, { timeout: 30000 });
        if (engineeringData.vessels.length) {
            await expect(page.locator('.vessel-section--engineering .vessel-toggle')).toHaveCount(engineeringData.vessels.length);
            await expect(page.locator('.vessel-section--engineering .vessel-empty')).toHaveCount(0);
            await checkOrder(page, 'engineering');
        } else {
            await expect(page.locator('.vessel-section--engineering .vessel-empty')).toBeVisible();
        }
        await expect(info).toHaveCount(1);
        await expect(sort).toHaveCount(0);
        await expect(info).not.toBeChecked();
        await expect(totalBadge).toHaveCount(0);
        await expect(page.locator('.vessel-info')).toHaveCount(0);
        await expect(page.locator('.vessel-history:visible')).toHaveCount(0);
        await expect(list).toHaveCSS('border-top-color', 'rgb(53, 167, 255)');
        await checkOrder(page, 'unloading');
        const listSize = await list.evaluate(element => ({ height: element.clientHeight, content: element.scrollHeight }));
        expect(listSize.content).toBeGreaterThan(listSize.height);
        expect(listSize.height).toBeLessThanOrEqual(416);
        await list.focus();
        await page.keyboard.press('ArrowDown');
        await expect.poll(() => list.evaluate(element => element.scrollTop)).toBeGreaterThan(0);

        await info.check();
        await expect(totalBadge).toHaveText(`${totalLabel} totalt tonn losset`);
        await expect(page.locator('.vessel-info')).toHaveCount(totalVesselCount);
        await expect(page.locator('.vessel-history:visible')).toHaveCount(0);
        const koralhav = page.locator('.vessel-item').filter({ has: page.locator('.vessel-name', { hasText: /^Koralhav$/ }) });
        await koralhav.getByRole('button').click();
        await expect(koralhav.locator('.vessel-history')).toBeVisible();
        await expect(koralhav.locator('tbody tr')).toHaveCount(data.vessels.find(v => v.name === 'Koralhav').entries.length);
        await expect(page.locator('.vessel-history:visible')).toHaveCount(1);
        await info.uncheck();
        await expect(totalBadge).toHaveCount(0);
        await expect(page.locator('.vessel-info')).toHaveCount(0);
        await expect(koralhav.locator('.vessel-history')).toBeVisible();
        await checkOrder(page, 'unloading');
        await koralhav.getByRole('button').press('Enter');
        await expect(page.locator('.vessel-history:visible')).toHaveCount(0);
        await info.check();
        const arctic = page.locator('.vessel-item').filter({ has: page.locator('.vessel-name', { hasText: /^Arctic Swan$/ }) });
        await arctic.getByRole('button').click();
        await expect(arctic.locator('.vessel-history')).toBeVisible();
        await page.evaluate(() => window.scrollTo(0, 0));
        if (process.env.VESSELS_SCREENSHOT_DIR) {
            await page.screenshot({ path: resolve(process.env.VESSELS_SCREENSHOT_DIR, 'vessels-desktop.png') });
        }
        for (const width of [360, 320]) {
            await page.setViewportSize({ width, height: 900 });
            const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
            expect(overflow, `No horizontal overflow at ${width}px`).toBe(false);
            expect(await list.evaluate(element => element.clientHeight)).toBeLessThanOrEqual(416);
        }
        if (process.env.VESSELS_SCREENSHOT_DIR) {
            await page.screenshot({ path: resolve(process.env.VESSELS_SCREENSHOT_DIR, 'vessels-mobile.png') });
        }

        // Fixture data stays in this browser; the saved engineering history is unchanged.
        const engineeringPage = await context.newPage();
        await engineeringPage.route('**/data/vessels/engineering.json', route => route.fulfill({ json: {
            schemaVersion: 1, category: 'engineering', vessels: ['Årvik', 'Bjørn', 'Ægir'].map((name, index) => ({
                id: `test-${index}`, name, entries: [{ id: `job-${index}`, periods: [{ start: '2026-09-20' }],
                    description: 'Test av instrumenter', tonnes: null, includeInTotal: false, sourceUrls: [] }],
            })),
        } }));
        await engineeringPage.goto(`${baseURL}/vessels`);
        await expect(engineeringPage.locator('.vessel-section--engineering .vessel-toggle')).toHaveCount(3);
        await checkOrder(engineeringPage, 'engineering');
        await engineeringPage.getByRole('switch').check();
        const engineeringBoat = engineeringPage.locator('.vessel-section--engineering .vessel-item').first();
        await expect(engineeringBoat.locator('.vessel-info')).toContainText('1 oppdrag');
        await expect(engineeringBoat.locator('.vessel-info')).not.toContainText('tonn');
        await engineeringBoat.getByRole('button').click();
        await expect(engineeringPage.getByRole('cell', { name: 'Test av instrumenter' })).toBeVisible();
        await engineeringPage.getByRole('switch').uncheck();
        await checkOrder(engineeringPage, 'engineering');
        await checkOrder(engineeringPage, 'unloading');
        await expect(engineeringPage.locator('.vessel-history:visible')).toHaveCount(1);

        // Both an HTTP failure and malformed hand-edited data must recover through Retry.
        for (const failure of [
            { status: 503, body: 'Unavailable' },
            { json: { schemaVersion: 1, category: 'unloading', vessels: [{ id: 'broken', name: 'Broken', entries: [{ id: 'job', periods: [] }] }] } },
        ]) {
            const retryPage = await context.newPage();
            let fail = true;
            await retryPage.route('**/data/vessels/unloading.json', route => fail ? route.fulfill(failure) : route.continue());
            await retryPage.goto(`${baseURL}/vessels`);
            await expect(retryPage.getByRole('alert')).toContainText('Arbeidshistorikken kunne ikke lastes');
            fail = false;
            await retryPage.getByRole('button', { name: 'Prøv igjen' }).click();
            await expect(retryPage.locator('.vessel-toggle')).toHaveCount(totalVesselCount);
            await expect(retryPage.getByRole('alert')).toHaveCount(0);
            await retryPage.close();
        }
        expect(errors).toEqual([]);
        console.log('Vessel browser checks passed: controls, sorting, expansion, engineering fixture, mobile layout and failure recovery.');
    } finally {
        await browser.close();
    }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
