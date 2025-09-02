import asyncio
import json
import logging
import os
import re
import tempfile
import time
from pathlib import Path

import zendriver as nodriver

# import nodriver
# import nodriver.core.connection as ndc
import zendriver.core.connection as ndc
from dotenv import load_dotenv
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


async def get_latest_reply() -> str:
    profile_name = "chatgpt"
    browser = await start_browser(headless=False, profile_name=profile_name)
    tab = browser.main_tab

    cookie_store = get_cookies_store(profile_name)

    await first_run_login(browser, tab, cookie_store, "https://chatgpt.com/auth/login")

    # 2️⃣  Navigate to the conversation
    # Get the conversation ID from the .env
    load_dotenv()
    cid = os.getenv("conversation_id")
    logging.info("Using conversation ID: %s", cid)
    await tab.get(f"https://chat.openai.com/c/{cid}")

    # 3️⃣  Poll the page every 500 ms until an assistant bubble exists
    logging.info("Waiting for the latest reply...")
    html = await get_html(tab)
    # Could refresh the page if it takes too long or conversation could not be loaded

    # 4️⃣  Convert HTML → Markdown
    logging.info("Converting HTML to Markdown...")
    markdown = md(html, strip=["span"]).strip()
    logging.info("Latest reply fetched successfully")

    # Stop browser
    await browser.stop()

    # try to capture a fenced ```json ... ``` block (tolerates "Copy code" noise)
    m = re.search(
        r"```(?:\s*json)?(?:\s*Copy code)?\s*(\{.*?\})\s*```",
        markdown,
        flags=re.S | re.I,
    )
    json_str = (
        m.group(1) if m else markdown[markdown.index("{") : markdown.rindex("}") + 1]
    )

    data = json.loads(json_str)
    title = data.get("title", None)
    description = data.get("description", None)
    logging.info("Latest reply title: %s", title)
    logging.info("Latest reply description: %s", description)

    # Save the results in /temp
    logging.info(
        "Saving the latest reply to a temp location: %s", tempfile.gettempdir()
    )
    (Path(tempfile.gettempdir()) / "latest_reply.md").write_text(markdown)

    return markdown, title, description


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    result = nodriver.loop().run_until_complete(get_latest_reply())
    print(result)

    # In case of 409 error try via googling: chatGPT and then logging in
