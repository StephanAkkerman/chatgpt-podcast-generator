# login.py
import asyncio
import logging
import time
import urllib.parse
from dataclasses import dataclass
from typing import Dict

import nodriver

from utils import get_cookies_store, start_browser

logger = logging.getLogger(__name__)


async def wait_until_host(tab: nodriver.Tab, target: str, timeout: int = 300):
    """Pause until `tab.url` lands on `target` (host only)."""
    start = time.time()
    while (time.time() - start) < timeout:
        host = urllib.parse.urlparse(tab.url).netloc
        if host == target:
            await asyncio.sleep(1)  # let UI settle
            return
        await asyncio.sleep(0.5)
    raise TimeoutError(f"Still not on {target} after {timeout}s (now on {host})")


@dataclass(frozen=True)
class Site:
    name: str
    login_url: str
    landing_host: str
    profile_name: str

    async def ensure_login(self) -> None:
        """Open browser profile; if no cookies, drive login flow."""
        browser = await start_browser(headless=False, profile_name=self.profile_name)
        tab = browser.main_tab
        cookie_store = get_cookies_store(self.profile_name)

        if cookie_store.exists():  # already logged-in
            logger.info("✅  %s cookies found → skipped login", self.name)
            return

        logger.info("🔑  %s: opening login page…", self.name)
        await tab.get(self.login_url)
        await wait_until_host(tab, self.landing_host)
        await browser.cookies.save(cookie_store)
        logger.info("✅  %s cookies saved to %s", self.name, cookie_store)


SITES: Dict[str, Site] = {
    "chatgpt": Site(
        name="ChatGPT",
        login_url="https://chatgpt.com/auth/login",
        landing_host="chatgpt.com",
        profile_name="chatgpt",
    ),
    "notebooklm": Site(
        name="NotebookLM",
        login_url="https://notebooklm.google.com",
        landing_host="notebooklm.google.com",
        profile_name="notebooklm",
    ),
    "spotify": Site(
        name="Spotify",
        login_url=(
            "https://creators.spotify.com/api/shell/gateway"
            "?locale=en&returnTo=%2Fdashboard%2Fepisode%2Fwizard"
            "&createAccountIfNecessary=false&showCreationMigration=true"
        ),
        landing_host="creators.spotify.com",
        profile_name="spotify",
    ),
}


async def main():
    # choose which site(s) to log into
    # await SITES["spotify"].ensure_login()  # single
    # or run several in parallel:
    await asyncio.gather(*(site.ensure_login() for site in SITES.values()))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    nodriver.loop().run_until_complete(main())
