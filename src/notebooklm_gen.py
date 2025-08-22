import argparse
import asyncio
import logging
import time
from pathlib import Path

from nodriver import loop

from utils import first_run_login, get_cookies_store, start_browser

DOWNLOAD_DIR = Path.home() / "Downloads"
TIMEOUT_S = 120  # 2-minute max

logger = logging.getLogger(__name__)


async def wait_for_download(dir_path: Path, timeout_s: int = 120):
    """
    Block until Chrome finishes every .crdownload in dir_path
    (or timeout).  Returns the final file path once complete.
    """
    t0 = time.perf_counter()
    final_path = None

    while True:
        # look for *.crdownload AND any new non-tmp file
        tmp_files = list(dir_path.glob("*.crdownload"))
        finished = [
            p
            for p in dir_path.iterdir()
            if not p.name.endswith(".crdownload") and p.stat().st_mtime > t0
        ]

        if not tmp_files and finished:
            # assume the most recent finished file is our WAV
            final_path = max(finished, key=lambda p: p.stat().st_mtime)
            break

        if time.perf_counter() - t0 > timeout_s:
            logger.warning("⏳  Timeout: no download finished in %s seconds", timeout_s)
            logger.warning("Not yet downloaded: %s", tmp_files)
            raise TimeoutError("Download did not finish in allotted time")

        await asyncio.sleep(0.5)  # poll twice a second

    return final_path


async def new_notebook(tab, md: str):
    # Locate "Create new notebook" button and click it
    logger.info("⏳  Creating new notebook…")
    # ── A. click the “My notebooks” toggle ────────────────────────────
    my_notebooks_button = await tab.find("Create new notebook")
    await my_notebooks_button.click()

    # ---- after you clicked “Create / New notebook” -------------------
    logger.info("⏳  Waiting for the new notebook dialog to appear…")
    copied_text = await tab.find("Copied text")
    await copied_text.click()
    logger.info("✅  Pressed copied text button.")

    logger.info("⏳  Waiting for the text input to appear…")
    textarea = await tab.find("textarea[formcontrolname='text']")
    await textarea.send_keys(md)  # TODO: make this quicker
    logger.info("✅  Updated text area.")

    # Submit the dialog form directly (works for every language / theme)
    await tab.evaluate("document.querySelector('form.content')?.requestSubmit()")
    logger.info("✅  Submitted input text.")

    # TODO: press the customize button on Audio Overview

    # Press the "Audio Overview" button
    AUDIO_BTN = "button.audio-overview-button"

    # wait until the button exists *and* is enabled
    logger.info("⏳  Waiting for the Audio Overview button to be enabled…")
    await tab.wait_for(AUDIO_BTN + ":not([disabled])", timeout=20_000)
    btn = await tab.select(AUDIO_BTN)  # → NodeHandle
    await btn.click()
    logger.info("✅  Pressed Audio Overview button.")


async def existing_notebook(tab):
    # For debugging, open an existing notebook
    logger.info("⏳  Opening existing notebook…")
    # ── A. click the “My notebooks” toggle ────────────────────────────
    my_notebooks_button = await tab.find("My notebooks")
    await my_notebooks_button.click()

    # ── 2. wait until at least one project-button card is in the DOM ───
    CARD_SEL = "project-button mat-card[role='button']"
    await tab.wait_for(CARD_SEL, timeout=20_000)

    # ── 3. click the FIRST tile (top-left = newest by default) ─────────
    first_card = await tab.select(CARD_SEL)
    await first_card.click()
    logger.info("✅  Opened existing notebook.")

    # Click the load button (only when the notebook does already exist)
    # logger.info("⏳  Waiting for the Load button to be enabled…")
    # LOAD_BTN = "button[aria-label='Load the Audio Overview']"  # unique attribute
    # await tab.wait_for(LOAD_BTN + ":not([disabled])", timeout=60_000)
    # await (await tab.select(LOAD_BTN)).click()
    # logger.info("✅  Load button clicked.")

    # ── 4. wait until the notebook view finishes loading ───────────────
    await tab.wait_for("button.audio-overview-button", timeout=20_000)
    logger.info("✅  Existing notebook opened")


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


async def generate_podcast(content: str):
    profile_name = "notebooklm"
    browser = await start_browser(headless=False, profile_name=profile_name)
    tab = browser.main_tab

    await tab.get("https://notebooklm.google.com")

    cookie_store = get_cookies_store(profile_name)

    # first‑run interactive login
    await first_run_login(browser, tab, cookie_store)

    # Create a new notebook
    await new_notebook(tab, content)

    # Debugging: use existing notebook
    # await existing_notebook(tab)

    # Wait until the "Audio Overview" button is enabled
    logger.info("⏳  Waiting for the audio controls menu to appear…")
    menu_button = "button.artifact-more-button"
    # Wait for the button to be ready
    await tab.wait_for(menu_button + ":not([disabled])", timeout=300_000)
    await (await tab.select(menu_button)).click()
    logger.info("✅  Menu opened.")

    logger.info("⏳  Looking for the download button")
    # Find the download button
    await (await tab.find("download")).click()
    logger.info("✅  Download triggered.")

    # Get the title
    logger.info("⏳  Looking for the notebook title and summary")
    title, summary = await get_title_and_summary(tab)
    logger.info("✅  Got notebook title and summary.")

    # # 1️⃣  You click the "Download" link in NotebookLM here …
    #     (the browser starts writing xxx.wav.crdownload)
    logger.info("⏳  Waiting for the download to finish…")
    wav_path = await wait_for_download(DOWNLOAD_DIR, TIMEOUT_S)
    logger.info("✅  Download ready → %s", wav_path)

    # Optional: head back to overview
    # Delete the last notebook

    # Stop browser
    browser.stop()

    return title, summary, wav_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a podcast using NotebookLM.")
    parser.add_argument(
        "content", type=str, help="The content to use for generating the notebook."
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    loop().run_until_complete(generate_podcast(args.content))
