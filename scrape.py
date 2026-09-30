import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import sys
import re
from collections import Counter

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
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"],  # kills navigator.webdriver
            )
            context = browser.new_context(
                user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"),
                viewport={"width": 1366, "height": 768},
                locale="en-US",
                timezone_id="America/Los_Angeles",
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=5000)   # let PX's JS run and set its cookie
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            browser.close()
    return soup


def count_words(soup: BeautifulSoup, words: list, skip_tags: list):
    pattern = re.compile(r"(?:" + "|".join(map(re.escape, words)) + r")", re.IGNORECASE)
    counts = Counter()
    for node in soup.find_all(string=pattern):
        if node.parent.name in skip_tags:
            continue
        for match in pattern.findall(node):
            counts[match.lower()] += 1
    return counts



def check_stock_markers(url: str, use_chromium: bool):
    soup = fetch_html(url, use_chromium)
    if not soup:
        print("Failed to fetch HTML content.")
        sys.exit(1)

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    # We have been detected as a bot. Fail out
    if "robot or human" in title.lower():
        print(f"Blocked by bot detection (page title: {title!r}). "
              "The site did not return the product page.")
        sys.exit(1)

    WORDS = ["Sold Out", "Out of Stock", "Unavailable", "Coming Soon"]
    SKIP_TAGS = {"script", "style", "noscript", "template"}

    counts = count_words(soup, WORDS, SKIP_TAGS)
    for word,count in counts.most_common():
        print(f"{word}: {count}")

check_stock_markers(url, use_chromium)
