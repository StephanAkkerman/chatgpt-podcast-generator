import asyncio
import logging
import time
import urllib.parse

import nodriver

from utils import get_cookies_store, start_browser


async def wait_until_host(tab, target_host: str, timeout_s: int = 300):
    """
    Block until `urllib.parse.urlparse(tab.url).netloc` == target_host
    or until `timeout_s` seconds elapse.

    Works regardless of how many third-party redirects happen in between.
    """
    start = time.time()
    while True:
        host = urllib.parse.urlparse(tab.url).netloc
        if host == target_host:
            # Give the main UI a moment to render
            await asyncio.sleep(1)
            return
        if time.time() - start > timeout_s:
            raise TimeoutError(
                f"Still not on {target_host} after {timeout_s}s (current host: {host})"
            )
        await asyncio.sleep(0.5)


async def chatgpt_login():
    """Logs you in to ChatGPT"""
    profile_name = "chatgpt"

    browser = await start_browser(headless=False, profile_name=profile_name)
    tab = browser.main_tab

    cookie_store = get_cookies_store(profile_name)

    if cookie_store.exists():
        return

    await tab.get("https://chatgpt.com/auth/login")
    landing_host: str = "chatgpt.com"
    await wait_until_host(tab, landing_host)
    await browser.cookies.save(cookie_store)
    logging.info("✅  Cookies saved to %s", cookie_store)


async def notebooklm_login():
    profile_name = "notebooklm"

    browser = await start_browser(headless=False, profile_name=profile_name)
    tab = browser.main_tab

    cookie_store = get_cookies_store(profile_name)

    if cookie_store.exists():
        return

    await tab.get("https://notebooklm.google.com")
    landing_host: str = "notebooklm.google.com"
    await wait_until_host(tab, landing_host)
    await browser.cookies.save(cookie_store)
    logging.info("✅  Cookies saved to %s", cookie_store)


async def spotify_login():
    profile_name = "spotify"

    browser = await start_browser(headless=False, profile_name=profile_name)
    tab = browser.main_tab

    cookie_store = get_cookies_store(profile_name)

    if cookie_store.exists():
        return

    await tab.get(
        "https://creators.spotify.com/api/shell/gateway?locale=en&returnTo=%2Fdashboard%2Fepisode%2Fwizard&createAccountIfNecessary=false&showCreationMigration=true"
    )
    landing_host: str = "creators.spotify.com"
    await wait_until_host(tab, landing_host)
    await browser.cookies.save(cookie_store)
    logging.info("✅  Cookies saved to %s", cookie_store)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    nodriver.loop().run_until_complete(spotify_login())
