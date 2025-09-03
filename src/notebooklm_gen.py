import asyncio
import logging
import tempfile
import time
from pathlib import Path
from typing import Iterable

# from nodriver import loop
from zendriver import loop

from utils import first_run_login, get_cookies_store, start_browser

DOWNLOAD_DIR = Path.home() / "Downloads"
TIMEOUT_S = 120  # 2-minute max

logger = logging.getLogger(__name__)


async def wait_for_download(
    dir_path: Path,
    timeout_s: int = 120,
    exts: Iterable[str] = (".wav", ".m4a", ".mp3"),
    poll_s: float = 0.5,
) -> Path:
    """
    Wait until a NEW file with one of `exts` is fully downloaded in `dir_path`.
    Detects Chrome's .crdownload and ignores pre-existing files.
    Returns the final Path.
    """
    dir_path = Path(dir_path)
    start_ts = time.time()  # EPOCH seconds (matches st_mtime)
    baseline = {p.name for p in dir_path.iterdir()}  # files that already existed

    deadline = start_ts + timeout_s
    last_sizes: dict[Path, int] = {}

    while True:
        # any active Chrome temp downloads?
        tmp_files = list(dir_path.glob("*.crdownload"))

        # candidates that are *new* (not in baseline) and with desired extension
        candidates = [
            p
            for p in dir_path.iterdir()
            if p.suffix.lower() in exts
            and p.name not in baseline
            and p.stat().st_mtime >= start_ts - 1  # allow 1s clock fuzz
        ]

        # if we have candidates and no temp files are present → likely finished
        if candidates and not tmp_files:
            newest = max(candidates, key=lambda p: p.stat().st_mtime)

            # Optional: double-check the size is stable across two polls
            size = newest.stat().st_size
            if last_sizes.get(newest) == size:
                return newest  # stable → done
            last_sizes[newest] = size
            # fall through to sleep then re-check

        # timeout?
        if time.time() > deadline:
            tmp_names = ", ".join(t.name for t in tmp_files) or "none"
            raise TimeoutError(
                f"Download did not finish in {timeout_s}s (tmp: {tmp_names})"
            )

        await asyncio.sleep(poll_s)


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


async def generate_podcast(content: str, debug_mode: bool = False):
    profile_name = "notebooklm"
    browser = await start_browser(headless=False, profile_name=profile_name)
    tab = browser.main_tab
    temp_dir = Path(tempfile.gettempdir())

    await tab.get("https://notebooklm.google.com")

    cookie_store = get_cookies_store(profile_name)

    # first‑run interactive login
    await first_run_login(browser, tab, cookie_store)

    # Use latest reply as content, if content is None
    if content is None:
        content = (temp_dir / "latest_reply.md").read_text()

    # Debugging: use existing notebook
    if debug_mode:
        await existing_notebook(tab)
    else:
        # Create a new notebook
        await new_notebook(tab, content)

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
    audio_path = await wait_for_download(DOWNLOAD_DIR, TIMEOUT_S)
    logger.info("✅  Download ready → %s", audio_path)

    # Optional: head back to overview
    # Delete the last notebook

    # Stop browser
    await browser.stop()

    # Save the title and summary

    (temp_dir / "notebook_title.txt").write_text(title)
    (temp_dir / "notebook_summary.txt").write_text(summary)

    return title, summary, audio_path


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    result = loop().run_until_complete(generate_podcast(None, debug_mode=True))
    print(result)
