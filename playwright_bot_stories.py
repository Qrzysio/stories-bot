import os
import random
import json
import time
import yaml
import requests
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError
)

# Directories
COOKIES_DIR = Path('/data/cookies')
CONFIG_PATH = Path("config.yaml")


# Constants
FB_HOME_URL = "https://business.facebook.com/latest/home"
STORY_COMPOSER_URL_FRAGMENT = "story_composer"


def load_config():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    return config.get("fb_profiles", {})


def download_image(url):
    try:
        print(f"[INFO] Downloading image from URL")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Let's check what this image is — let's look at Content-Type
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            return None, f"URL does not point to an image (Content-Type: {content_type})"

        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_file.write(response.content)
        temp_file.close()
        print(f"[SUCCESS] Image downloaded to temp file: {temp_file}")
        return temp_file.name, None
    except Exception:
        print(f"[ERROR] Failed to download image from URL")
        return None


def is_url_valid(text: str) -> bool:
    try:
        parsed = urlparse(text)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


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
            return False
    print(f"[SUCCESS] Loaded cookies for service {service_id}")
    return True


def check_for(name, selector_list, page):
    wait = None

    for selector_text in selector_list:
        try:
            wait = page.wait_for_selector(f"{selector_text}", timeout=10000)
            print(f"[SUCCESS] {name} - complete")
            break
        except PlaywrightTimeoutError:
            print(f"[WARNING] {name} - NEGATIVE")

    if wait is None:
        print(f"[WARNING] {name} on any language - NEGATIVE")
        return False

    return True


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
            if btn:
                break
        except Exception:
            print(f"[WARNING] Could not click ({text})")

    if not btn:
        print("[ERROR] Could not click button in any language")

    return btn


def post_story(service_id: str, image_path: str, link: str = None, headless: bool = True):
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
            context.close()
            browser.close()
            raise Exception(f"Cookies file not found for {service_id}")


        page = context.new_page()
        # Go to FB home with asset_id to open composer directly
        page.goto(f"{FB_HOME_URL}?asset_id={service_id}", timeout=60000)

        # Verify login
        name = "Login"
        selector_list = ["a[aria-label='Strona główna'] >> text=Strona główna", "a[aria-label='Home'] >> text=Home"]
        if not check_for(name, selector_list, page):
            context.close()
            browser.close()
            raise Exception(f"{name} - negative")

        # Click "Create Story"
        text_list = ["Utwórz relację", "Create Story"]
        btn = hover_btn(page, browser, text_list)
        if not btn:
            context.close()
            browser.close()
            raise Exception(f"Click 'Create Story' btn failed")
        btn.click()


        # Wait for composer
        page.wait_for_url(f"**/{STORY_COMPOSER_URL_FRAGMENT}/**", timeout=15000)
        print("[SUCCESS] Story composer loaded")

        # Click "Add photo/video" with Filechooser interception
        text_list = ["Dodaj zdjęcie/film", "Add photo/video"]
        btn = hover_btn(page, browser, text_list)
        if not btn:
            context.close()
            browser.close()
            raise Exception(f"Click 'Add photo/video' btn failed")
        try:
            with page.expect_file_chooser() as fc_info:
                btn.click()
            file_chooser = fc_info.value
            file_chooser.set_files(str(image_path))
            print("[INFO] File selected for upload via filechooser")
        except Exception:
            print(f"[ERROR] Filechooser interception failed")
            context.close()
            browser.close()
            raise Exception(f"Filechooser interception failed")

        # Wait for preview
        timeout = 30000
        selector = 'img.img[src*="scontent"]'
        deadline = time.time() + timeout / 1000

        while time.time() < deadline:
            try:
                element = page.query_selector(selector)
                if element:
                    print(f"[SUCCESS] Visible photo preview")
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if not element:
            print(f"[WARNING] {name} — превью не появилось за {timeout} мс.")

        # Link input
        if link:
            link_texts = ["Dodaj link", "Edytuj link", "Add link", "Edit link"]
            btn = hover_btn(page, browser, link_texts)
            if not btn:
                context.close()
                browser.close()
                raise Exception(f"Click 'Add link' btn failed")
            btn.click()
            try:
                input_field = page.wait_for_selector("input[type='url']", timeout=5000)
                input_field.fill("")
                time.sleep(random.randint(1, 3))
                input_field.type(link, delay=random.randint(100, 150))
                print(f"[SUCCESS] Link inputed: {link}")
            except Exception:
                print(f"[ERROR] Can't find link input field")
                context.close()
                browser.close()
                raise Exception(f"Can't find link input field")

                # Click "Apply"
            apply_texts = ["Zastosuj", "Apply"]
            btn = hover_btn(page, browser, apply_texts)
            if not btn:
                context.close()
                browser.close()
                raise Exception(f"Click 'Apply' btn failed")
            btn.click()

        # Simulation Tab 6 + Enter
        print("[INFO] Simulation Tab x6 + Enter")
        try:
            for _ in range(6):
                page.keyboard.press("Tab")
                time.sleep(0.2)
            time.sleep(random.randint(1, 3))
            page.keyboard.press("Enter")
            print("[SUCCESS] Simulation - complete")
            time.sleep(random.randint(10, 15))
        except Exception:
            print(f"[ERROR] Simulation Tab x6 + Enter - negative")
            context.close()
            browser.close()
            raise Exception(f"Simulation Tab x6 + Enter - negative")


        # Check for published
        try:
            content_url = f"https://business.facebook.com/latest/content_calendar?asset_id={service_id}"
            page.wait_for_url(content_url, timeout=10000)
            print(f"[SUCCESS] Story published on {content_url}")
        except PlaywrightTimeoutError:
            print("[WARNING] Story DOES NOT published")
            raise Exception(f"Story DOES NOT published")

        context.close()
        browser.close()
