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
    "--disable-automation",  # redundant but harmless
    "--disable-infobars",
    "--allow-running-insecure-content",
    "--disable-features=ChromeWhatsNewUI",  # keeps the “What’s new” tab closed
]

PROFILE_DIR = Path.cwd() / "chrome_profile"
COOKIE_STORE = PROFILE_DIR / "cookies.json"


async def start_browser(headless: bool) -> nodriver.Browser:
    """Launch nodriver with our persistent profile."""
    browser = await nodriver.start(
        headless=headless,
        no_sandbox=True,
        user_data_dir=PROFILE_DIR,
        browser_args=EXTRA_ARGS,  # ← pass the full list here
    )
    print(f"🔍  Browser started with profile: {PROFILE_DIR}")

    # Load the cookies if they exist
    if COOKIE_STORE.exists():
        await browser.cookies.load(COOKIE_STORE)
        print(f"🔑  Cookies loaded from: {COOKIE_STORE}")
    else:
        print("🔑  No cookies found, starting fresh session.")

    return browser
