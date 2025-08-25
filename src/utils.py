import asyncio
import logging
import sys
from pathlib import Path

# import nodriver
import zendriver as zd

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
    max_tries: int = 3,
) -> zd.Browser:
    """Launch nodriver with a persistent profile, with retries & cleanup."""
    profile_dir = get_profile_dir(profile_name)
    profile_dir.mkdir(parents=True, exist_ok=True)

    last_exc = None
    for attempt in range(1, max_tries + 1):
        try:
            browser = await zd.start(
                headless=headless,
                no_sandbox=True,  # important when running as root
                user_data_dir=profile_dir,
                browser_args=EXTRA_ARGS,
            )
            # Load cookies if present
            cookies_store = get_cookies_store(profile_name, cookies_file)
            if cookies_store.exists():
                await browser.cookies.load(cookies_store)
                logger.info("🔑  Cookies loaded from %s", cookies_store)

            logger.info("✅ Browser started (try %d/%d)", attempt, max_tries)
            return browser

        except Exception as e:
            last_exc = e
            logger.warning(
                "Browser start failed (try %d/%d): %s", attempt, max_tries, e
            )

            # small backoff (exponential)
            await asyncio.sleep(1.5 * attempt)

    raise RuntimeError(f"Failed to start browser after {max_tries} tries: {last_exc}")


async def first_run_login(browser, tab, cookie_store, custom_url=None) -> None:
    if cookie_store.exists():
        logger.info("Found existing cookies at %s", cookie_store)
        await browser.cookies.load(cookie_store)
        return

    if custom_url:
        await tab.get(custom_url)

    logger.info("🔑  First run — log in in the opened window.")
    if sys.stdin.isatty():
        logger.info("After logging in, press <ENTER> here.")
        await asyncio.to_thread(input)
    else:
        logger.info("Running headless; this is not yet supported…")

    await browser.cookies.save(cookie_store)
    logger.info("✅  Cookies saved to %s", cookie_store)
