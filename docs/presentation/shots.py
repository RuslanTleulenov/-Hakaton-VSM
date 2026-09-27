"""Скриншоты интерфейса для презентации: снимаем реальные экраны тренажёра."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://localhost:8040"


def shot(page, name, clip_selector=None, top=False):
    if top:
        page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(700)
    path = OUT / f"{name}.png"
    if clip_selector:
        page.locator(clip_selector).screenshot(path=str(path))
    else:
        page.screenshot(path=str(path))
    print("saved", path)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1180, "height": 900}, device_scale_factor=2)
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(1200)

    # 1. каталог: рейс недели и рейсы смены
    shot(page, "01-catalog")

    # 2. лайт-новелла: сцена с персонажем
    page.locator("[data-trip='day-751']").click()
    page.wait_for_timeout(1500)
    shot(page, "02-novel")

    # 3. ход сделан: причины и шкалы
    page.locator(".option").first.click()
    page.wait_for_timeout(1200)
    shot(page, "03-after-move")

    # 4. интермедия между инцидентами с памятью рейса
    for _ in range(6):
        if page.locator("#next-segment").count():
            break
        buttons = page.locator(".option")
        if buttons.count():
            buttons.first.click()
            page.wait_for_timeout(900)
    if page.locator("#next-segment").count():
        shot(page, "04-segment-done")

    # 5. разбор: доигрываем отдельный сценарий до конца
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(1000)
    page.locator("[data-start='medical']").click()
    page.wait_for_timeout(1200)
    for option in ["ask", "radio", "empathy", "breathing"]:
        target = page.locator(f"[data-option='{option}']")
        if target.count():
            target.click()
        else:
            page.locator(".option").first.click()
        page.wait_for_timeout(900)
    page.wait_for_timeout(900)
    shot(page, "05-debrief")
    page.evaluate("window.scrollTo(0, 900)")
    shot(page, "06-debrief-events")

    # 6. профиль и рейтинг
    page.evaluate("document.querySelector('[data-view=\"profile\"]').click()")
    shot(page, "07-profile", top=True)
    page.evaluate("document.querySelector('[data-view=\"leaderboard\"]').click()")
    shot(page, "08-leaderboard", top=True)
    page.evaluate("document.querySelector('[data-view=\"analytics\"]').click()")
    shot(page, "09-analytics", top=True)

    browser.close()
print("done")
