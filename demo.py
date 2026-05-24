"""
הרצה חזותית של Playwright — ללא API key
פותח דפדפן ושולף תחזית מזג אוויר לעיר שתבחרי
"""
import asyncio
from playwright.async_api import async_playwright

CITY = "תל אביב"   # ← שני את שם העיר כאן
URL  = "https://www.weather2day.co.il/forecast"

SEARCH_SELECTORS = [
    "input[type='search']",
    "input[role='combobox']",
    "[class*='search' i] input",
    "input[placeholder*='חיפ']",
    "input[placeholder*='עיר']",
    "input[placeholder*='מיקום']",
    "header input[type='text']",
    "nav input[type='text']",
    "form input[type='text']",
]

DROPDOWN_SELECTORS = [
    "[role='option']:first-child",
    "[role='listbox'] [role='option']:first-child",
    "[role='listbox'] li:first-child",
    "[class*='autocomplete' i] li:first-child",
    "[class*='suggest' i] li:first-child",
    "[class*='result' i] li:first-child",
    "[class*='dropdown' i] li:first-child",
    "ul[class*='list' i] li:first-child",
]


async def demo():
    print(f"\n🌐  פותח דפדפן ומנווט ל-{URL}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=600)
        page = await browser.new_page(
            locale="he-IL",
            viewport={"width": 1280, "height": 800},
        )

        await page.goto(URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        print(f"✅  הדף נטען: {await page.title()}")

        # --- מחפש שדה חיפוש ---
        found_input = False
        for sel in SEARCH_SELECTORS:
            el = page.locator(sel).first
            if await el.count() > 0 and await el.is_visible():
                print(f"🔍  מוצא שדה חיפוש ({sel}) ומקליד: {CITY}")
                await el.click()
                await el.fill(CITY)
                await page.wait_for_timeout(1800)
                found_input = True
                break

        if not found_input:
            print("⚠️  לא נמצא שדה חיפוש — השאר הדפדפן פתוח לבדיקה ידנית")
            input("לחץ Enter לסגירה...")
            return

        # --- בוחר מהרשימה ---
        found_dropdown = False
        for sel in DROPDOWN_SELECTORS:
            el = page.locator(sel).first
            if await el.count() > 0 and await el.is_visible():
                print(f"📋  בוחר פריט ראשון מהרשימה ({sel})")
                await el.click()
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(2500)
                found_dropdown = True
                break

        if not found_dropdown:
            print("⚠️  לא נמצאה רשימה נפתחת — משאיר דפדפן פתוח")
            input("לחץ Enter לסגירה...")
            return

        print(f"\n🎉  הגענו לדף התחזית!")
        print(f"🔗  URL: {page.url}")
        print(f"📄  כותרת: {await page.title()}")

        print("\n⏳  הדפדפן יישאר פתוח 30 שניות — תסתכלי על התחזית...")
        await page.wait_for_timeout(30_000)

        await browser.close()
        print("✅  סגור.")


if __name__ == "__main__":
    asyncio.run(demo())
