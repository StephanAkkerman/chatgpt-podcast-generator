#!/usr/bin/env python3
"""
Turn a local Markdown file into a NotebookLM Audio-Overview .wav file.

First run shows Chrome so you can log in.
After you hit <ENTER> in the terminal, cookies are written to COOKIE_STORE
and every later run is fully headless + unattended.

Usage:
    python notebooklm_gen.py
"""

import asyncio
import pathlib
import time

from nodriver import loop

from utils import first_run_login, get_cookies_store, start_browser


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


async def element_text(el) -> str:
    """Return trimmed textContent from a nodriver Element handle."""
    # 1️⃣ property on recent versions
    if hasattr(el, "text"):
        return el.text.strip()

    # 2️⃣ coroutine on a few releases
    if hasattr(el, "inner_text"):
        return (await el.inner_text()).strip()

    # 3️⃣ universal fallback
    return await el._tab.evaluate("(e) => e.textContent.trim()", el)


async def get_notebook_summary(tab) -> str:
    """
    Return the full summary paragraph (including <strong> parts).
    """
    # Wait until the paragraph is in the DOM
    await tab.wait_for(".summary-content p", timeout=10_000)

    # One-shot JS IIFE → returns full innerText
    # TODO: save with HTML tags like <strong>
    summary = await tab.evaluate(
        """
        (() => {
            const p = document.querySelector('.summary-content p');
            return p ? p.innerText.trim() : '';
        })()
    """
    )
    return summary


async def get_title_and_summary(tab):
    # ---- title ----
    await tab.wait_for("h1.notebook-title", timeout=10_000)
    title_el = await tab.select("h1.notebook-title")
    title = await element_text(title_el)

    # ---- summary ----
    summary = await get_notebook_summary(tab)

    return title, summary


async def run(md_file: pathlib.Path):
    profile_name = "notebooklm_gen"
    browser = await start_browser(headless=False, profile_name=profile_name)
    tab = browser.main_tab

    await tab.get("https://notebooklm.google.com")

    cookie_store = get_cookies_store(profile_name)

    # first‑run interactive login
    await first_run_login(browser, tab, cookie_store)

    # Create a new notebook
    # await new_notebook(tab, md_file.read_text(encoding="utf-8"))

    # Debugging: use existing notebook
    await existing_notebook(tab)

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

    # Get the title
    title, summary = await get_title_and_summary(tab)

    # For debugging, save the title and summary to files
    output_path = pathlib.Path("tmp/title.txt")
    output_path.write_text(title, encoding="utf-8")
    print(f"✅  Saved the title to {output_path}")

    summary_path = pathlib.Path("tmp/summary.txt")
    summary_path.write_text(summary, encoding="utf-8")
    print(f"✅  Saved the summary to {summary_path}")

    # Optional: head back to overview
    # Delete the last notebook

    # Debugging: Keep the browser open
    await asyncio.get_running_loop().run_in_executor(None, input)

    return title, summary


if __name__ == "__main__":
    loop().run_until_complete(run(pathlib.Path("tmp/output.txt")))
