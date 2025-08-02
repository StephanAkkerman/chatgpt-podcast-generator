import asyncio
from pathlib import Path

import nodriver

EXTRA_ARGS = [
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-extensions",
    "--disable-notifications",
    "--disable-popup-blocking",
    "--start-maximized",
    "--disable-logging",
    "--log-level=3",
    "--silent",
    "--disable-infobars",
    "--allow-running-insecure-content",
    "--disable-features=ChromeWhatsNewUI",  # keeps the “What’s new” tab closed
]


def get_profile_dir(profile_name: str = "chrome_profile") -> Path:
    """Return the path to the Chrome profile directory."""
    return Path.cwd() / profile_name


def get_cookies_store(
    profile_name: str = "chrome_profile", cookies_file: str = "cookies.json"
) -> Path:
    return get_profile_dir(profile_name) / cookies_file


async def start_browser(
    profile_name: str = "chrome_profile",
    cookies_file: str = "cookies.json",
    headless: bool = False,
) -> nodriver.Browser:
    """Launch nodriver with our persistent profile."""
    profile_dir = get_profile_dir(profile_name)

    browser = await nodriver.start(
        headless=headless,
        no_sandbox=True,
        user_data_dir=profile_dir,
        browser_args=EXTRA_ARGS,
    )
    print(f"🔍  Browser started with profile: {profile_dir}")

    cookies_store = get_cookies_store(profile_name, cookies_file)

    # Load the cookies if they exist
    if cookies_store.exists():
        await browser.cookies.load(cookies_store)
        print(f"🔑  Cookies loaded from: {cookies_store}")
    else:
        print("🔑  No cookies found, starting fresh session.")

    return browser


async def first_run_login(browser, tab, cookie_store, custom_url: str = None) -> None:
    if not cookie_store.exists():
        if custom_url:
            await tab.get(custom_url)

        print("🔑  First run — log in / pass CAPTCHA in the opened window.")
        print("When you see the NotebookLM home screen, press <ENTER> here.")

        # 3️⃣  Block until the user presses Enter *without* freezing the event loop
        await asyncio.get_running_loop().run_in_executor(None, input)

        # Save the cookies
        await browser.cookies.save(cookie_store)
        print("✅  Cookies saved to", cookie_store)
    else:
        print(f"Found existing cookies at {cookie_store}")
