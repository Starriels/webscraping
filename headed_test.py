"""Diagnostic: open Walmart in a *visible* Chromium and report what PX sees.

If this passes (title is the product name) but headless fails -> fingerprint problem.
If this also fails -> IP reputation problem; fingerprint tweaks won't help.
"""
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else (
    "https://www.walmart.com/ip/Nintendo-Switch-2-The-Legend-of-Zelda-40th-Anniversary-Edition/21002656445"
)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="en-US")
    page = ctx.new_page()
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)  # give PX time; watch the window

    print("TITLE:    ", page.title())
    print("webdriver:", page.evaluate("navigator.webdriver"))
    print("UA:       ", page.evaluate("navigator.userAgent"))
    print("PX cookie:", any(c["name"].startswith("_px") for c in ctx.cookies()))

    input("Press Enter to close the browser...")
    browser.close()
