#!/usr/bin/env python3
"""
Fetch the newest assistant message from a ChatGPT conversation using nodriver.

• First run opens Chrome, you log in by hand, script saves cookies.
• Later runs are headless and reuse the saved cookies.

Usage
-----
python chatgpt_pull.py
"""
import asyncio
import time

import nodriver
import nodriver.core.connection as ndc
from markdownify import markdownify as md

from utils import first_run_login, get_cookies_store, start_browser


async def get_html(tab: nodriver.Tab) -> str:

    async def html_of_last_bubble() -> str | None:
        return await tab.evaluate(
            """(() => {
            const els = document.querySelectorAll('[data-message-author-role="assistant"]');
            if (!els.length) return null;                      // not ready yet
            const last = els[els.length - 1];
            const box  = last.querySelector('.markdown') || last;
            return box.innerHTML;
        })()"""
        )

    html = None
    while html is None:
        if time.perf_counter() > time.perf_counter() + 60:  # 60‑second timeout
            raise TimeoutError("No assistant message after 60 s")
        try:
            html = await html_of_last_bubble()
        except ndc.ProtocolException as e:
            if "node with given id" in str(e):
                # Page navigated → DOM id cache invalid; just retry
                continue
            raise
        await asyncio.sleep(0.5)

    return html


async def get_latest_reply(cid: str) -> str:
    profile_name = "chatgpt_pull"
    browser = await start_browser(headless=False, profile_name=profile_name)
    tab = browser.main_tab

    cookie_store = get_cookies_store(profile_name)

    await first_run_login(browser, tab, cookie_store, "https://auth.openai.com/log-in")

    # 2️⃣  Navigate to the conversation
    await tab.get(f"https://chat.openai.com/c/{cid}")

    # 3️⃣  Poll the page every 500 ms until an assistant bubble exists
    html = await get_html(tab)

    # 4️⃣  Convert HTML → Markdown
    markdown = md(html, strip=["span"]).strip()

    # Save the markdown to /tmp/chatgpt_reply.md
    with open("tmp/output.txt", "w") as text_file:
        text_file.write(markdown)
    print("✅  Saved the newest assistant reply to tmp/output.txt")


if __name__ == "__main__":
    cid = "6855081e-83e8-8005-81bd-bdd27276805e"  # TODO: move to config

    # nodriver's own helper avoids "event loop closed" issues on Windows
    loop = nodriver.loop()
    output = loop.run_until_complete(get_latest_reply(cid))

    # In case of 409 error try via googling: chatGPT and then logging in
