#!/usr/bin/env python3
"""
markdown2mp3_notebooklm.py  –  nodriver edition
Turn a local Markdown file into a NotebookLM Audio‑Overview MP3.

First run shows Chrome so you can log in.
After you hit <ENTER> in the terminal, cookies are written to COOKIE_STORE
and every later run is fully headless + unattended.

Usage:
    python markdown2mp3_notebooklm.py /absolute/path/to/file.md
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import time

import requests
from nodriver import loop, start

# ─── user‑tweakables ────────────────────────────────────────────────────────
PROFILE_DIR = r"E:\GitHub\finance-podcast-generator\notebooklm_profile"
COOKIE_STORE = pathlib.Path(PROFILE_DIR) / "notebooklm_cookies.json"
HEADLESS = False
OUT_DIR = pathlib.Path.cwd() / "podcasts"
OUT_DIR.mkdir(exist_ok=True)

SEL = {
    "create": "button:text('Create new notebook'), button:text('新規作成')",
    "addnote": "button:text('Add note'), button:text('メモを追加')",
    "textarea": "textarea[formcontrolname='newNote']",
    "insert": "button:text('Insert'), button:text('挿入')",
    "spinner": ".mat-progress-spinner",
    "generate": "button:text('Generate'), button:text('生成')",
    "more": "button[aria-label*='options']",
    "download": "a[mat-menu-item]:text('Download'), a[mat-menu-item]:text('ダウンロード')",
}

CREATE_SELECTORS = [
    "button:text('Create new notebook')",  # English 2024 UI
    "button:text('New notebook')",  # English 2025 UI
    "button[aria-label='Create new notebook']",
    "button[aria-label='New notebook']",
    "button:text('新規作成')",  # Japanese UI
]


async def first_selector(tab, sels, timeout=5000) -> str | None:
    """Return the first selector that exists, or None."""
    for sel in sels:
        try:
            await tab.wait_for(sel, timeout=timeout)
            return sel
        except Exception:
            continue
    return None


async def click(tab, target, timeout=120_000):
    """Click by selector (str) or by NodeHandle returned from tab.find()."""
    if isinstance(target, str):
        await tab.wait_for(target, timeout=timeout)
        handle = await tab.select(target)
    else:  # assume ElementHandle
        handle = target
    await handle.click()


# ─── main worker ────────────────────────────────────────────────────────────
async def run(md_file: pathlib.Path):

    browser = await start(
        headless=HEADLESS,
        no_sandbox=True,
        user_data_dir=PROFILE_DIR,
        browser_args=["--disable-dev-shm-usage", "--disable-features=ChromeWhatsNewUI"],
    )
    tab = browser.main_tab

    # 1️⃣ If we already have cookies, load them
    if COOKIE_STORE.exists():
        await browser.cookies.load(COOKIE_STORE)

    await tab.get("https://notebooklm.google.com")

    # ── first‑run interactive login ────────────────────────────────────────
    if not COOKIE_STORE.exists():
        print("🔑  First run — log in / pass CAPTCHA in the opened window.")
        print("When you see the NotebookLM home screen, press <ENTER> here.")

        # 3️⃣  Block until the user presses Enter *without* freezing the event loop
        await asyncio.get_running_loop().run_in_executor(None, input)

        # Save the cookies
        await browser.cookies.save(COOKIE_STORE)
        print("✅  Cookies saved to", COOKIE_STORE)

    md = md_file.read_text()

    # Locate "Create new notebook" button and click it
    sel = await first_selector(tab, CREATE_SELECTORS)
    if not sel:
        raise RuntimeError("Create‑notebook button not found – UI changed?")
    await click(tab, sel)

    # ---- after you clicked “Create / New notebook” -------------------
    copied_text = await tab.find("Copied text")
    await copied_text.click()

    textarea = await tab.find("textarea[formcontrolname='text']")
    await textarea.send_keys(md)  # Very slow

    # Click the insert button
    INSERT_BTN = "button[textContent='Insert']"
    # await tab.wait_for(INSERT_BTN, timeout=10_000)
    h = await tab.select(INSERT_BTN)
    await h.click()

    await asyncio.get_running_loop().run_in_executor(None, input)

    await click(tab, SEL["generate"], timeout=240_000)
    await tab.wait_for(SEL["more"], timeout=300_000)
    await tab.click(SEL["more"])
    href = await tab.get_attribute(SEL["download"], "href")
    if not href:
        raise RuntimeError("Download link missing!")

    # ── download MP3 with same cookies ─────────────────────────────────────
    # sess = load_cookies_to_requests()
    # mp3_path = OUT_DIR / f"{int(time.time())}.mp3"
    # print("⬇️  downloading…")
    # with sess.get(href, stream=True, timeout=120) as r:
    #     r.raise_for_status()
    #     with open(mp3_path, "wb") as f:
    #         for chunk in r.iter_content(8192):
    #             f.write(chunk)
    # print(f"🎧  Saved → {mp3_path}")

    await browser.stop()


# ─── entry‑point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    loop().run_until_complete(run(pathlib.Path("tmp/output.txt")))
