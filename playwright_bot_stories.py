import os
import random
import json
import string
import subprocess
import time

import validators
import yaml
import requests
import tempfile
from io import BytesIO
from PIL import Image
from pathlib import Path
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
ACCEPTED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_IMAGE_SIZE = 2 * 1024 * 1024


def load_config():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    return config.get("fb_profiles", {})


def validate_image_from_url(url):
    try:
        print("[INFO] Validating image from URL...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Сontent type validation
        content_type = response.headers.get('Content-Type', '')
        if content_type not in ACCEPTED_MIME_TYPES:
            return None, f"Unsupported Content-Type format (Content-Type: {content_type})"

        # File size validation
        if len(response.content) > 2 * 1024 * 1024:
            return None, "Image size exceeds MAX_IMAGE_SIZE limit"

        # Damage check
        image_bytes = BytesIO(response.content)
        try:
            img = Image.open(image_bytes)
            img.verify()  # Damage check
        except Exception as e:
            return None, f"Image failed verification: {e}"

        # Image format validation
        img = Image.open(image_bytes)
        if img.format not in ("JPEG", "PNG", "WEBP"):
            return None, f"Unsupported image format (actual format: {img.format})"

        # Image size validation
        image_bytes.seek(0)
        img = Image.open(image_bytes)
        if img.height <= img.width:
            return None, "Image is not portrait (height must be greater than width)"

        return response.content, None  # Return the content to save for later

    except requests.HTTPError as http_err:
        return None, f"HTTP error: {http_err}"
    except requests.RequestException as req_err:
        return None, f"Request error: {req_err}"
    except Exception as e:
        return None, f"Unexpected error: {e}"

def download_image(image_bytes):
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_file.write(image_bytes)
        temp_file.close()
        print(f"[SUCCESS] Image saved to temp file: {temp_file.name}")
        return temp_file.name, None
    except Exception as e:
        # Delete the file if it was created
        if temp_file is not None:
            try:
                os.remove(temp_file.name)
            except Exception as cleanup_err:
                print(f"[WARNING] Failed to remove temp file: {cleanup_err}")
        return None, f"Failed to save image to temp file: {e}"


def convert_to_mp4(input_file):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
        output_file = temp_video_file.name


    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        audio_file = temp_audio_file.name

    try:

        cmd_audio = [
            "ffmpeg",
            "-y",
            "-f", "lavfi",
            "-i", "anoisesrc=color=white:amplitude=0.001:r=44100",
            "-t", "10",
            "-q:a", "9",
            audio_file
        ]
        result_audio = subprocess.run(cmd_audio, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result_audio.returncode != 0:
            os.remove(audio_file)
            return None, f"ffmpeg error (audio generation): {result_audio.stderr}"


        cmd_video = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", input_file,
            "-i", audio_file,
            "-shortest",
            "-t", "10",
            "-c:v", "libx264",
            "-profile:v", "high",
            "-level", "4.1",
            "-crf", "34",
            "-preset", "faster",
            "-g", "60",
            "-r", "30",
            "-c:a", "aac",
            "-b:a", "64k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease",
            output_file
        ]
        result_video = subprocess.run(cmd_video, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


        if os.path.exists(audio_file):
            os.remove(audio_file)

        if result_video.returncode != 0:
            if os.path.exists(output_file):
                os.remove(output_file)
            return None, f"ffmpeg error (video generation): {result_video.stderr}"

        return output_file, None

    except Exception as e:
        if os.path.exists(output_file):
            os.remove(output_file)
        if os.path.exists(audio_file):
            os.remove(audio_file)
        return None, str(e)


def is_url_valid(text: str) -> bool:
    return validators.url(text) is True


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


def check_for(name, selector_list, page, timeout=6000):
    wait = None

    for selector_text in selector_list:
        try:
            wait = page.wait_for_selector(f"{selector_text}", timeout=timeout)
            print(f"[SUCCESS] {name} - complete")
            break
        except PlaywrightTimeoutError:
            print(f"[WARNING] {name} - NEGATIVE")

    if wait is None:
        print(f"[WARNING] {name} on any language - NEGATIVE")
        return False

    return True


def hover_btn(
        page,
        browser,
        text_list,
        timeout=15000,
        locator=None
):

    btn = None

    for text in text_list:
        try:
            if not locator:
                locator = page.locator(f"div[role=button]:has-text('{text}')").first
            locator.wait_for(state="visible", timeout=timeout)
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


def type_random_then_clear(page):
    count = random.randint(1, 5)
    chars = ''.join(random.choices(string.ascii_letters, k=count))

    for c in chars:
        page.keyboard.type(c)
        time.sleep(random.uniform(0.2, 0.9))
    time.sleep(random.uniform(1, 2.8))
    for _ in range(count):
        page.keyboard.press("Backspace")
        time.sleep(random.uniform(0.2, 0.9))


def post_story(service_id: str, image_path: str, num_tabs: int, link: str = None, headless: bool = True):
    with sync_playwright() as p:

        # Launch browser

        # browser = p.chromium.launch(
        #     headless=headless,
        #     args = [
        #         "--disable-notifications",
        #         "--disable-infobars",
        #         "--no-default-browser-check",
        #     ]
        # )
        browser = p.firefox.launch(
            headless=headless,
            firefox_user_prefs={
                "dom.webnotifications.enabled": False,  # отключаем push-уведомления
                "permissions.default.desktop-notification": 2,
                "dom.push.enabled": False,
                "signon.rememberSignons": False,  # отключаем диалог сохранения пароля
                "browser.shell.checkDefaultBrowser": False,
                "browser.aboutHomeSnippets.updateUrl": "",
                "browser.startup.homepage_override.mstone": "ignore",
                "browser.startup.homepage_welcome_url": "about:blank"
            },
            args=[
                "--no-default-browser-check",
                "--disable-infobars",
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
        page.goto(f"{FB_HOME_URL}?asset_id={service_id}", timeout=180000)

        # Verify login
        name = "Login"
        selector_list = ["a[aria-label='Strona główna'] >> text=Strona główna", "a[aria-label='Home'] >> text=Home"]
        if not check_for(name, selector_list, page, 180000):
            context.close()
            browser.close()
            raise Exception(f"{name} - negative")

        # Update cookies
        try:
            cookies = context.cookies()
            save_cookies_json(service_id, cookies)
            print(f"[INFO] Cookies refreshed for {service_id}")
        except Exception as e:
            print(f"[WARNING] Failed to refresh cookies for {service_id}: {e}")

        # Click "Create Story"
        text_list = ["Utwórz relację", "Create Story"]
        btn = hover_btn(page, browser, text_list, 300000)
        if not btn:
            context.close()
            browser.close()
            raise Exception(f"Click 'Create Story' btn failed")
        btn.click()

        # Wait for composer
        page.wait_for_url(f"**/{STORY_COMPOSER_URL_FRAGMENT}/**", timeout=180000)
        print("[SUCCESS] Story composer loaded")

        # Click "Add photo/video" with Filechooser interception
        text_list = ["Dodaj zdjęcie/film", "Add photo/video"]
        btn = hover_btn(page, browser, text_list, 300000)
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
        timeout = 7000
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
            time.sleep(random.uniform(1, 4))
        if not element:
            print(f"[WARNING] {name} — no prewiev for {timeout} ms.")

        # Link input
        if link:
            btn_texts = ["Dodaj link", "Edytuj link", "Add link", "Edit link"]
            btn = hover_btn(page, browser, btn_texts, 300000)
            if not btn:
                context.close()
                browser.close()
                raise Exception(f"Click 'Add link' btn failed")
            btn.click()
            try:
                input_field = page.wait_for_selector("input[type='url']", timeout=700000)
                # input_field.fill("")
                time.sleep(random.uniform(1, 3))
                input_field.fill(link)
                time.sleep(random.uniform(1, 2))
                # input_field.type(link, delay=random.uniform(10, 30))
                # value = input_field.input_value()
                # if value != link:
                #     print("[WARNING] Link typed incorrectly, retrying...")
                #     input_field.fill(link)
                # time.sleep(random.uniform(1, 3))
                print(f"[SUCCESS] Link inputed: {link}")
            except Exception:
                print(f"[ERROR] Can't find link input field")
                context.close()
                browser.close()
                raise Exception(f"Can't find link input field")

                # Click "Apply"
            apply_texts = ["Zastosuj", "Apply"]
            btn = hover_btn(page, browser, apply_texts, 700000)
            if not btn:
                context.close()
                browser.close()
                raise Exception(f"Click 'Apply' btn failed")
            btn.click()


        # Edd sticker
        if link and num_tabs == 8:

            # Press btn Edytuj
            time.sleep(random.uniform(1, 2))
            btn_texts = ["Edytuj", "Edit"]
            btn = hover_btn(page, browser, btn_texts, 300000)
            if not btn:
                context.close()
                browser.close()
                raise Exception(f"Click 'Edytuj' btn failed")
            btn.click()

            # Press btn Naklejki
            time.sleep(random.uniform(0.5, 1))
            btn_texts = ["Naklejki", "Stickers"]
            btn = hover_btn(page, browser, btn_texts, 300000)
            if not btn:
                context.close()
                browser.close()
                raise Exception(f"Click 'Naklejki' btn failed")
            btn.click()

            # Press btn Link
            time.sleep(random.uniform(0.5, 2))
            btn_texts = ["Link", ]
            locator = page.locator("div[role=button][aria-label='Create link sticker']")
            btn = hover_btn(page, browser, btn_texts, 300000, locator)
            if not btn:
                context.close()
                browser.close()
                raise Exception(f"Click 'Link' btn failed")
            btn.click()
            time.sleep(random.uniform(0.5, 2))

            # Insert link
            for _ in range(2):
                page.keyboard.press("Tab")
                time.sleep(random.uniform(0.3, 1))

            time.sleep(random.uniform(1, 2))
            page.evaluate(f"""() => {{
                const el = document.activeElement;
                el.value = "{link}";
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}""")
            type_random_then_clear(page)

            # Check link insertion
            current_value = page.evaluate("() => document.activeElement.value")
            if current_value != link:
                raise Exception(f"[ERROR] Sticker Link was not inserted! Current value: {current_value}")
            else:
                print(f"[SUCCESS] Sticker Link inputed: {link}")

            # Click first "Apply"
            for _ in range(2):
                page.keyboard.press("Tab")
                time.sleep(random.uniform(0.3, 1))

            time.sleep(random.uniform(1, 2))
            page.keyboard.press("Enter")
            time.sleep(random.uniform(2, 3))

            # Click second "Apply"
            apply_texts = ["Zastosuj", "Apply"]
            btn = hover_btn(page, browser, apply_texts, 700000)
            if not btn:
                context.close()
                browser.close()
                raise Exception(f"Click 'Apply' btn failed")
            btn.click()

        # Simulation Tab + Enter
        print("[INFO] Simulation Tab + Enter")
        time.sleep(random.uniform(1, 4))
        try:
            for _ in range(num_tabs):
                page.keyboard.press("Tab")
                time.sleep(random.uniform(0.5, 1))
            time.sleep(random.uniform(1, 3))
            page.keyboard.press("Enter")
            print("[SUCCESS] Simulation - complete")
        except Exception:
            print(f"[ERROR] Simulation Tab + Enter - negative")
            context.close()
            browser.close()
            raise Exception(f"Simulation Tab + Enter - negative")

        # Check for published
        try:
            page.wait_for_url("**/*content_calendar*", timeout=300000)
            print(f"[SUCCESS] Story published successfully")
        except PlaywrightTimeoutError:
            print("[WARNING] Story DOES NOT published")
            raise Exception(f"Story DOES NOT published")

        # Close browser
        context.close()
        browser.close()