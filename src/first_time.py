import logging

import nodriver

from utils import first_run_login, get_cookies_store, start_browser


async def chatgpt_login():
    """Logs you in to ChatGPT"""
    profile_name = "chatgpt_pull"

    browser = await start_browser(headless=False, profile_name=profile_name)
    tab = browser.main_tab

    cookie_store = get_cookies_store(profile_name)

    # first‑run interactive login
    await first_run_login(browser, tab, cookie_store, "https://chatgpt.com/auth/login")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    nodriver.loop().run_until_complete(chatgpt_login())
