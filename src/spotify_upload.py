import argparse
import logging
from pathlib import Path

from nodriver import loop

from utils import first_run_login, get_cookies_store, start_browser

logger = logging.getLogger(__name__)


def latest_audio(downloads: Path | None = None) -> Path:
    """Return newest .wav or .m4a in the folder (default: ~/Downloads)."""
    downloads = downloads or (Path.home() / "Downloads")
    candidates = [
        p
        for p in downloads.iterdir()
        if p.is_file() and p.suffix.lower() in {".wav", ".m4a"}
    ]
    if not candidates:
        raise FileNotFoundError("No .wav or .m4a files found in Downloads")
    return max(candidates, key=lambda p: p.stat().st_mtime)


async def upload_podcast(title: str, summary: str, audio_path: Path):
    profile_name = "spotify"
    browser = await start_browser(profile_name=profile_name)
    tab = browser.main_tab

    await tab.get("https://creators.spotify.com/pod/dashboard/episode/wizard")

    # Get the cookies store
    cookie_store = get_cookies_store(profile_name=profile_name)

    # first‑run interactive login
    await first_run_login(browser, tab, cookie_store)

    # Upload the last .wav file
    await tab.wait_for("input[type='file']", timeout=10_000)
    file_input = await tab.select("input[type='file']")  # Element handle

    # 3.  inject file *without* opening the OS chooser
    # TODO: get the lastest .wav of .m4a file (take the most recent of either)
    await file_input.send_file(audio_path)
    logger.info("⏫  upload started: %s", audio_path)

    # Fill in the title
    textarea = await tab.find("input[name='title']")
    await textarea.send_keys(title)

    # Click the HTML button for the description
    btn = await tab.find("HTML")
    await btn.click()

    # Focus the content-editable box
    await tab.wait_for("textarea[name='description']", timeout=10_000)
    box = await tab.find("textarea[name='description']")
    await box.click()

    # Type the summary
    await box.send_keys(summary)
    logger.info("📝  Description field filled")

    # Click "Next" button (bottom right)
    await (await tab.find("Next")).click()

    # wait until the “Now” option is rendered
    await tab.wait_for("label[for='publish-date-now']", timeout=10_000)

    # click the label – automatically selects the underlying radio button
    await (await tab.select("label[for='publish-date-now']")).click()

    # Wait for the publish button to be ready
    PUBLISH_SEL = "button[type='submit'][form='review-form']"
    await tab.wait_for(PUBLISH_SEL + ":not([disabled])", timeout=60_000)
    await (await tab.select(PUBLISH_SEL)).click()

    # Remove the .wav file from the local disk
    audio_path.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a podcast to Spotify.")
    parser.add_argument("title", type=str, help="The title of the podcast episode.")
    parser.add_argument(
        "summary", type=str, help="The summary/description of the podcast episode."
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    loop().run_until_complete(upload_podcast(args.title, args.summary, latest_audio()))
