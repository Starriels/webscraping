import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import sys
import re

url = sys.argv[1]

use_chromium = sys.argv[2].lower() == "true" if len(sys.argv) > 2 else False


def fetch_html(url:str, use_chromium:bool):
    if not use_chromium:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
    else:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],  # kills navigator.webdriver
            )
            context = browser.new_context(
                user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"),
                viewport={"width": 1366, "height": 768},
                locale="en-US",
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)   # let PX's JS run and set its cookie
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            browser.close()
    return soup

soup = fetch_html(url, use_chromium)

title = soup.title.string.strip() if soup.title and soup.title.string else ""
# We have been detected as a bot. Fail out
if "robot or human" in title.lower():
    print(f"Blocked by bot detection (page title: {title!r}). "
          "The site did not return the product page.")
    sys.exit(1)

words = ["Sold Out", "Out of Stock", "Unavailable"]

# Creates the pattern string: (?:apple|banana|cherry)
pattern_string = r"(?:" + "|".join(words) + r")"
pattern = re.compile(pattern_string, re.IGNORECASE)
results = soup.find_all(string=pattern)
if not results:
    print("No results found")
else:
    for result in results:
        print(result.strip())

