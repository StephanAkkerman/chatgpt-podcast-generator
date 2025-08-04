import asyncio
import logging
import sys
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

logger = logging.getLogger(__name__)


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
    logger.info("🔍  Browser started with profile: %s", profile_dir)

    cookies_store = get_cookies_store(profile_name, cookies_file)

    # Load the cookies if they exist
    if cookies_store.exists():
        await browser.cookies.load(cookies_store)
        logger.info("🔑  Cookies loaded from: %s", cookies_store)
    else:
        logger.info("🔑  No cookies found, starting fresh session.")

    return browser


async def manual_checkpoint():
    """Block until the user presses ENTER *or* Ctrl-C."""
    prompt = "Log in, then press ENTER (or Ctrl-C) here… "
    try:
        # off-load to a thread so the event-loop stays alive
        await asyncio.to_thread(input, prompt)
    except (KeyboardInterrupt, EOFError):
        # Ctrl-C or closed stdin ==> treat as “continue”
        print("")  # newline so prompt looks finished
        logger.info("Manual checkpoint skipped via Ctrl-C/EOF")


async def first_run_login(browser, tab, cookie_store, custom_url=None) -> None:
    if cookie_store.exists():
        logger.info("Found existing cookies at %s", cookie_store)
        await browser.cookies.load(cookie_store)
        return

    if custom_url:
        await tab.get(custom_url)

    logger.info("🔑  First run — log in in the opened window.")
    if sys.stdin.isatty():
        await manual_checkpoint()
    else:
        logger.info("Running headless; this is not yet supported…")

    await browser.cookies.save(cookie_store)
    logger.info("✅  Cookies saved to %s", cookie_store)
