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
    "--logging-level=3",
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


# ------------------------------------------------------------------------
async def wait_for_login_signal(prompt="logging in, then press ENTER or Ctrl-C here…"):
    """
    Suspend until the user either
      • presses ENTER  (normal stdin)   OR
      • hits Ctrl-C    (SIGINT)         OR
      • closes the terminal (EOF)
    The coroutine resumes without raising KeyboardInterrupt, so your
    script continues smoothly.
    """
    import signal

    loop = asyncio.get_running_loop()
    fut = loop.create_future()

    # 1️⃣  SIGINT handler (Ctrl-C)
    def _on_sigint():
        if not fut.done():
            fut.set_result(None)  # wake the future

    loop.add_signal_handler(signal.SIGINT, _on_sigint)

    # 2️⃣  stdin reader in background thread (ENTER / EOF)
    async def _stdin_task():
        try:
            await asyncio.to_thread(input, prompt)
        except EOFError:
            pass
        if not fut.done():
            fut.set_result(None)

    asyncio.create_task(_stdin_task())

    # 3️⃣  Wait until one of the two completes
    await fut

    # 4️⃣  Clean up
    loop.remove_signal_handler(signal.SIGINT)


# ------------------------------------------------------------------------
async def first_run_login(browser, tab, cookie_store: Path, login_url: str):
    """
    • If cookies exist → load them, return.
    • Otherwise open login_url, let user sign in, wait for signal, save cookies.
    """
    if cookie_store.exists():
        await browser.cookies.load(cookie_store)
        logging.info("✅  Cookies loaded from %s", cookie_store)
        return

    await tab.get(login_url)
    logging.info("🔑  First run — logging in in the opened window.")
    if sys.stdin.isatty():
        await wait_for_login_signal()  # handles ENTER *or* Ctrl-C
    else:
        logging.info("No interactive TTY; waiting until UI shows login…")
        # optional: implement DOM polling fallback here
        raise RuntimeError("Headless login not yet implemented")

    await browser.cookies.save(cookie_store)
    logging.info("✅  Cookies saved to %s", cookie_store)
