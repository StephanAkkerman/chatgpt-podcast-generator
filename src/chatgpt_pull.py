#!/usr/bin/env python3
"""
Fetch the newest assistant message from a ChatGPT conversation using nodriver.

• First run opens Chrome, you log in by hand, script saves cookies.
• Later runs are headless and reuse the saved cookies.

Usage
-----
python chatgpt_pull.py <conversation_id>
"""
import asyncio
import time
from pathlib import Path

import nodriver
import nodriver.core.connection as ndc
from markdownify import markdownify as md

CHAT = "https://chat.openai.com"
PROFILE_DIR = r"E:\GitHub\finance-podcast-generator\chat_profile"
COOKIE_STORE = Path(PROFILE_DIR) / "chat_cookies.json"
FIRST_RUN = not COOKIE_STORE.exists()


async def start_browser(headless: bool):
    """Launch nodriver with our persistent profile."""
    return await nodriver.start(
        headless=headless,
        no_sandbox=True,
        user_data_dir=PROFILE_DIR,
        browser_args=[
            "--disable-dev-shm-usage",
            "--disable-features=ChromeWhatsNewUI",
        ],
    )


async def newest_reply(cid: str) -> str:
    browser = await start_browser(headless=False)
    tab = browser.main_tab

    # 1️⃣  If we already have cookies, load them
    if COOKIE_STORE.exists():
        await browser.cookies.load(COOKIE_STORE)

    # 3️⃣  On first run, wait until the user finishes login + Cloudflare
    if FIRST_RUN:
        print("🔑  First-time setup … a Chrome window will open on the login page.")

        # 1️⃣  Send the tab straight to the Auth0 login form
        await tab.get("https://auth.openai.com/log-in")

        # 2️⃣  Tell the user what to do
        print(
            "\n"
            "➡️  Please sign in with your OpenAI account.\n"
            "   • solve any Cloudflare / CAPTCHA checks\n"
            "   • wait until the normal ChatGPT interface (or your task thread) is visible\n"
            "   • then come back to this terminal and PRESS <ENTER>\n"
        )

        # 3️⃣  Block until the user presses Enter *without* freezing the event loop
        await asyncio.get_running_loop().run_in_executor(None, input)  # unlimited time

        # 4️⃣  Persist the whole cookie jar for future headless runs
        await browser.cookies.save(COOKIE_STORE)
        print("✅  Cookies saved → future runs will be auto-logged-in.")

    # 2️⃣  Navigate to the conversation
    await tab.get(f"{CHAT}/c/{cid}")

    # 3️⃣  Poll the page every 500 ms until an assistant bubble exists

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
    deadline = time.perf_counter() + 60  # 60‑second timeout
    while html is None:
        if time.perf_counter() > deadline:
            raise TimeoutError("No assistant message after 60 s")
        try:
            html = await html_of_last_bubble()
        except ndc.ProtocolException as e:
            if "node with given id" in str(e):
                # Page navigated → DOM id cache invalid; just retry
                continue
            raise
        await asyncio.sleep(0.5)

    # 4️⃣  Convert HTML → Markdown
    markdown = md(html, strip=["span"]).strip()

    # Save the markdown to /tmp/chatgpt_reply.md
    with open("tmp/output.txt", "w") as text_file:
        text_file.write(markdown)
    print("✅  Saved the newest assistant reply to tmp/output.txt")


if __name__ == "__main__":
    cid = "6855081e-83e8-8005-81bd-bdd27276805e"

    # nodriver's own helper avoids "event loop closed" issues on Windows
    loop = nodriver.loop()
    output = loop.run_until_complete(newest_reply(cid))
