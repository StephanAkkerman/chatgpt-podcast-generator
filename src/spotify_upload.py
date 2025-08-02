import asyncio
import pathlib
from pathlib import Path

import nodriver
from nodriver import loop

from utils import first_run_login, get_cookies_store, start_browser


def latest_wav(downloads: Path | None = None) -> Path:
    """Return newest *.wav in the given folder (or ~/Downloads)."""
    downloads = downloads or (Path.home() / "Downloads")
    wavs = sorted(
        downloads.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not wavs:
        raise FileNotFoundError("No .wav files in Downloads")
    return wavs[0]


async def main():
    profile_name = "spotify_upload"
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

    wav_path = latest_wav()

    # 3.  inject file *without* opening the OS chooser
    await file_input.send_file(wav_path)
    print("⏫  upload started:", wav_path)

    # Fill in the title using the title.txt file
    title = pathlib.Path("tmp/title.txt").read_text(encoding="utf-8")
    textarea = await tab.find("input[name='title']")
    await textarea.send_keys(title)

    # Click the HTML button for the description
    btn = await tab.find("HTML")
    await btn.click()

    # -------- 1.  load the description text ---------------------------------
    desc = pathlib.Path("tmp/summary.txt").read_text(encoding="utf-8")
    # -------- 2.  focus the content-editable box ----------------------------
    await tab.wait_for("textarea[name='description']", timeout=10_000)
    box = await tab.find("textarea[name='description']")
    await box.click()

    # -------- 4.  type the description (one call, Slate receives real input)-
    await box.send_keys(desc)
    print("📝  Description field filled")

    # Maybe fill in the episode number?

    # Click "Next" button

    # Set the publish date radio button to now

    # Click the "Publish" button

    # Remove the .wav file from the local disk

    # Debugging: Keep the browser open
    await asyncio.get_running_loop().run_in_executor(None, input)


if __name__ == "__main__":
    loop().run_until_complete(main())
