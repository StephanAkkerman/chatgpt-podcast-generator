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

import asyncio
import pathlib
import time

from nodriver import loop

from utils import COOKIE_STORE, start_browser


async def new_notebook(tab, md: str):
    # Locate "Create new notebook" button and click it
    print("⏳  Creating new notebook…")
    # ── A. click the “My notebooks” toggle ────────────────────────────
    my_notebooks_button = await tab.find("Create new notebook")
    await my_notebooks_button.click()

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

    # Click the load button (only when the notebook does already exist)
    LOAD_BTN = "button[aria-label='Load the Audio Overview']"  # unique attribute
    await tab.wait_for(LOAD_BTN + ":not([disabled])", timeout=60_000)
    await (await tab.select(LOAD_BTN)).click()

    # ── 4. wait until the notebook view finishes loading ───────────────
    await tab.wait_for("button.audio-overview-button", timeout=20_000)
    print("✅  Existing notebook opened")


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


async def run(md_file: pathlib.Path):

    browser = await start_browser(headless=False)
    tab = browser.main_tab

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

    await new_notebook(tab, md_file.read_text(encoding="utf-8"))

    # await existing_notebook(tab)

    # Wait for the spinner to disappear
    # 1. Wait for spinner gone
    print("⏳  Waiting for spinner to disappear…")
    await wait_until_gone(tab, ".mat-progress-spinner", timeout_ms=300_000)
    print("✅  Spinner gone.")

    # ─── 1. open the “more options” menu ───────────────────────────────
    print("⏳  Waiting for the audio controls menu to appear…")
    await (await tab.select("button.audio-controls-button.menu-button")).click()
    print("✅  Menu opened.")

    await (await tab.select("a[download]")).click()
    print("✅  Download triggered.")

    # TODO: remove the notebook from the overview
    return


if __name__ == "__main__":
    loop().run_until_complete(run(pathlib.Path("tmp/output.txt")))
