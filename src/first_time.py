# login.py
import asyncio
import logging
import signal
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import zendriver as nodriver  # a.k.a. nodriver

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


class CookieAutoSaver:
    """Periodically save cookies to disk (atomic) until stopped."""

    def __init__(
        self, browser: nodriver.Browser, store_path: Path, interval_sec: float = 3.0
    ):
        self.browser = browser
        self.store_path = store_path
        self.interval = interval_sec
        self._task: Optional[asyncio.Task] = None
        self._stopping = asyncio.Event()

    async def _save_once_atomic(self):
        tmp = self.store_path.with_suffix(self.store_path.suffix + ".tmp")
        await self.browser.cookies.save(tmp)
        tmp.replace(self.store_path)

    async def _runner(self):
        # First save ASAP so users who close quickly still get a file.
        try:
            await self._save_once_atomic()
        except Exception as e:
            logger.debug("Initial cookie save failed (will retry): %s", e)

        while not self._stopping.is_set():
            try:
                await self._save_once_atomic()
            except Exception as e:
                # Happens briefly during navigation / process restarts; just retry next tick.
                logger.debug("Cookie save error (will retry): %s", e)
            try:
                await asyncio.wait_for(self._stopping.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                pass

        # Final best-effort save
        try:
            await self._save_once_atomic()
        except Exception as e:
            logger.warning("Final cookie save failed: %s", e)

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._runner())
        return self

    async def stop(self):
        if self._task:
            self._stopping.set()
            try:
                await self._task
            finally:
                self._task = None


@dataclass(frozen=True)
class Site:
    name: str
    login_url: str
    landing_host: str
    profile_name: str

    async def ensure_login(self) -> None:
        """
        Open browser profile; if no cookie file exists, drive login flow.
        While the browser is open, cookies are saved every 3s and once on shutdown.
        """
        cookie_store = get_cookies_store(self.profile_name)

        if cookie_store.exists():
            logger.info("✅  %s cookies found → skipped login", self.name)
            return

        browser = await start_browser(headless=False, profile_name=self.profile_name)
        tab = browser.main_tab

        saver = CookieAutoSaver(browser, cookie_store, interval_sec=3.0).start()

        # graceful shutdown: save once on SIGINT/SIGTERM then close browser
        async def shutdown():
            logger.info("🔻 Shutting down %s session…", self.name)
            await saver.stop()
            try:
                await browser.cookies.save(cookie_store)  # extra belt & braces
            except Exception:
                pass
            try:
                await browser.stop()
            except Exception:
                pass

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(
                    sig, lambda s=sig: asyncio.create_task(shutdown())
                )
            except NotImplementedError:
                # Windows fallback: signals may not be supported; ignore here.
                pass

        try:
            logger.info("🔑  %s: opening login page…", self.name)
            await tab.get(self.login_url)
            await wait_until_host(tab, self.landing_host)
            logger.info(
                "➡️  Landed on %s — you can continue navigating.", self.landing_host
            )
            logger.info("💾  Cookies will be auto-saved every 3s to: %s", cookie_store)
            logger.info("🧹  Press Ctrl-C to stop when you're done.")

            # Keep the session alive until user stops it (Ctrl-C)
            # or until the browser dies (errors will break the sleep).
            while True:
                await asyncio.sleep(3600)

        except asyncio.CancelledError:
            # Triggered by our signal handler
            pass
        except Exception as e:
            logger.warning("Session ended with error: %s", e)
        finally:
            await shutdown()


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
    # pick which to run; you can also run all in parallel with gather(...)
    # await SITES["chatgpt"].ensure_login()
    await asyncio.gather(*(site.ensure_login() for site in SITES.values()))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s"
    )
    nodriver.loop().run_until_complete(main())
