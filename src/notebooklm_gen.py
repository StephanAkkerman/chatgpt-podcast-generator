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
import pathlib
import time

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


async def new_notebook(tab, md: str):
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

    # Submit the dialog form directly (works for every language / theme)
    await tab.evaluate("document.querySelector('form.content')?.requestSubmit()")

    # Press the "Audio Overview" button
    AUDIO_BTN = "button.audio-overview-button"

    # wait until the button exists *and* is enabled
    await tab.wait_for(AUDIO_BTN + ":not([disabled])", timeout=20_000)

    btn = await tab.select(AUDIO_BTN)  # → NodeHandle
    await btn.click()


async def existing_notebook(tab):
    # For debugging, open an existing notebook
    print("⏳  Opening existing notebook…")
    # ── A. click the “My notebooks” toggle ────────────────────────────
    my_notebooks_button = await tab.find("My notebooks")
    await my_notebooks_button.click()

    # ── 2. wait until at least one project-button card is in the DOM ───
    CARD_SEL = "project-button mat-card[role='button']"
    await tab.wait_for(CARD_SEL, timeout=20_000)

    # ── 3. click the FIRST tile (top-left = newest by default) ─────────
    first_card = await tab.select(CARD_SEL)
    await first_card.click()


async def wait_until_gone(tab, selector: str, timeout_ms: int = 300_000):
    """
    Poll until `selector` no longer matches anything in the DOM.
    Works with nodriver because the JS is a function string.
    """
    esc = selector.replace("\\", "\\\\").replace("'", "\\'")
    js = f"() => !!document.querySelector('{esc}')"  # ⇦ function form

    t0 = time.perf_counter()
    while True:
        still_there = await tab.evaluate(js)  # returns bool
        if not still_there:
            return  # element gone
        if (time.perf_counter() - t0) * 1000 > timeout_ms:
            raise TimeoutError(f"{selector} still present after {timeout_ms/1000:.0f}s")
        await asyncio.sleep(0.5)


async def wait_for_blob_href(tab, timeout_s=30):
    JS = """(() => {
        const a = document.querySelector('a[mat-menu-item][download]');
        return a ? a.getAttribute('href') || '' : '';
    })()"""
    t0 = time.perf_counter()
    while True:
        href = await tab.evaluate(JS)  # returns str or ''
        if href.startswith("blob:"):
            return href
        if time.perf_counter() - t0 > timeout_s:
            raise TimeoutError("Download link never got a blob: href")
        await asyncio.sleep(0.5)


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

    # await new_notebook(tab, md_file.read_text(encoding="utf-8"))

    await existing_notebook(tab)

    # Click the load button (only when the notebook does already exist)
    # ── wait for the “Load” CTA to appear and be enabled ───────────────
    LOAD_BTN = "button[aria-label='Load the Audio Overview']"  # unique attribute
    await tab.wait_for(LOAD_BTN + ":not([disabled])", timeout=60_000)

    # ── click it ───────────────────────────────────────────────────────
    await (await tab.select(LOAD_BTN)).click()

    # ── 4. wait until the notebook view finishes loading ───────────────
    await tab.wait_for("button.audio-overview-button", timeout=20_000)
    print("✅  Existing notebook opened")

    # Wait for the spinner to disappear
    # 1. Wait for spinner gone
    print("⏳  Waiting for spinner to disappear…")
    await wait_until_gone(tab, ".mat-progress-spinner", timeout_ms=300_000)
    print("✅  Spinner gone.")

    # ─── 1. open the “more options” menu ───────────────────────────────
    print("⏳  Waiting for the audio controls menu to appear…")
    MENU_BTN = "button.audio-controls-button.menu-button"  # class is stable
    await (await tab.select(MENU_BTN)).click()
    print("✅  Menu opened.")

    await (await tab.select("a[download]")).click()
    print("✅  Download triggered.")

    # TODO: remove the notebook
    return


if __name__ == "__main__":
    loop().run_until_complete(run(pathlib.Path("tmp/output.txt")))
