import os
import random
import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Directories
COOKIES_DIR = Path('/data/cookies')
PHOTOS_DIR = Path('/data/uploads')


# Constants
FB_HOME_URL = "https://business.facebook.com/latest/home"
STORY_COMPOSER_URL_FRAGMENT = "story_composer"


def save_cookies_json(service_id, cookies):
    os.makedirs(COOKIES_DIR, exist_ok=True)
    cookie_file = os.path.join(COOKIES_DIR, f'{service_id}.json')
    with open(cookie_file, 'w') as f:
        json.dump(cookies, f)
    print(f"[SUCCESS] Cookies (JSON) for service {service_id} saved to {cookie_file}.")


def load_cookies(context, service_id: str):
    cookie_file = COOKIES_DIR / f"{service_id}.json"
    if not cookie_file.is_file():
        print(f"[ERROR] Cookies file not found: {cookie_file}")
        return False
    with cookie_file.open('r') as f:
        cookies = json.load(f)
    # Convert to Playwright cookie format
    for c in cookies:
        try:
            # Remove unsupported fields
            c_play = {k: c[k] for k in ('name', 'value', 'domain', 'path', 'expires', 'httpOnly', 'secure') if k in c}
            context.add_cookies([c_play])
        except Exception as e:
            print(f"[WARNING] Failed to add cookie {c.get('name')}: {e}")
    print(f"[SUCCESS] Loaded cookies for service {service_id}")
    return True


def check_for(name, selector_text, page):
    try:
        page.wait_for_selector(f"{selector_text}", timeout=10000)
        print(f"[SUCCESS] {name} - complete")
        return True
    except PlaywrightTimeoutError:
        print(f"[WARNING] {name} - NEGATIVE")
        return False


def hover_btn(page, browser, text_list):
    btn = None
    for text in text_list:
        try:
            locator = page.locator(f"div[role=button]:has-text('{text}')").first
            locator.wait_for(state="visible", timeout=7000)
            time.sleep(0.3)
            locator.scroll_into_view_if_needed()
            locator.hover()
            btn = locator
            break
        except Exception as e:
            print(f"[WARNING] Could not click ({text}): {e}")

    if not btn:
        print("[ERROR] Could not click button in any language")
        browser.close()
        sys.exit(1)

    return btn


def post_story(service_id: str, image_path: str, link: str = None, headless: bool = True):

    # Image path
    image_path = PHOTOS_DIR / image_path
    if not image_path.is_file():
        print(f"[ERROR] Image file not found: {image_path}")
        sys.exit(1)

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(
            headless=headless,
            args = [
                "--disable-notifications",
                "--disable-infobars",
                "--no-default-browser-check",
            ]
        )
        context = browser.new_context()

        # Load cookies
        if not load_cookies(context, service_id):
            browser.close()
            sys.exit(1)

        page = context.new_page()
        # Go to FB home with asset_id to open composer directly
        page.goto(f"{FB_HOME_URL}?asset_id={service_id}", timeout=60000)

        # Verify login
        name = "Login"
        selector_text = "a[aria-label=Home] >> text=Home"
        if not check_for(name, selector_text, page):
            browser.close()
            sys.exit(1)

        # Click "Create Story"
        text_list = ["Create Story", "Utwórz relację"]
        btn = hover_btn(page, browser, text_list)
        btn.click()

        # Wait for composer
        page.wait_for_url(f"**/{STORY_COMPOSER_URL_FRAGMENT}/**", timeout=15000)
        print("[SUCCESS] Story composer loaded")

        # Click "Add photo/video" with Filechooser interception
        text_list = ["Add photo/video", "Dodaj zdjęcie/wideo"]
        btn = hover_btn(page, browser, text_list)
        try:
            with page.expect_file_chooser() as fc_info:
                btn.click()
            file_chooser = fc_info.value
            file_chooser.set_files(str(image_path))
            print("[INFO] File selected for upload via filechooser")
        except Exception as e:
            print(f"[ERROR] Filechooser interception failed: {e}")
            browser.close()
            sys.exit(1)

        # Wait for preview
        time.sleep(random.randint(10,20))
        name = "Visible photo preview"
        selector_text = "img[src*='fbcdn']"
        checked = check_for(name, selector_text, page)

        # Link input
        if link:
            link_texts = ["Add link", "Dodaj link", "Edit link", "Edytuj link"]
            btn = hover_btn(page, browser, link_texts)
            btn.click()
            try:
                input_field = page.wait_for_selector("input[type='url']", timeout=5000)
                input_field.fill("")
                time.sleep(random.randint(1, 3))
                input_field.type(link, delay=random.randint(100, 150))
                print(f"[SUCCESS] Link inputed: {link}")
            except Exception as e:
                print(f"[ERROR] Can't find link input field {e}")
                return

                # Click "Apply"
            apply_texts = ["Apply", "Zastosuj"]
            btn = hover_btn(page, browser, apply_texts)
            btn.click()

        # Симуляция нажатий Tab 6 раз и Enter
        print("[INFO] Simulation Tab x6 + Enter")
        try:
            for _ in range(6):
                page.keyboard.press("Tab")
                time.sleep(0.2)
            time.sleep(random.randint(1, 3))
            page.keyboard.press("Enter")
            print("[SUCCESS] Simulation - complete")
            time.sleep(random.randint(10, 15))
        except Exception as e:
            print(f"[ERROR] Simulation - negative: {e}")


        # Check for published
        try:
            content_url = f"https://business.facebook.com/latest/content_calendar?asset_id={service_id}"
            page.wait_for_url(content_url, timeout=10000)
            print(f"[SUCCESS] Story published on {content_url}")
        except PlaywrightTimeoutError:
            print("[WARNING] Story DOES NOT published")

        context.close()
        browser.close()


if __name__ == "__main__":
   post_story(image_path="test.jpg", link="https://example.com", service_id="713714068490626", headless=False)
