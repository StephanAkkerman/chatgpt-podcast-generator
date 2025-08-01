import asyncio
import pathlib
import time
from pathlib import Path

import nodriver
import nodriver.core.connection as ndc
from markdownify import markdownify as md
from nodriver import loop, start

from utils import start_browser

# ─── user‑tweakables ────────────────────────────────────────────────────────
PROFILE_DIR = (
    r"E:\GitHub\finance-podcast-generator\spotify_profile"  # TODO: use local path
)
COOKIE_STORE = pathlib.Path(PROFILE_DIR) / "spotify_cookies.json"
HEADLESS = False


async def main():
    browser = await start_browser(headless=HEADLESS, profile_dir=PROFILE_DIR)


# Head to the spotify upload page
"https://creators.spotify.com/pod/dashboard/episode/wizard"

# Click "Select a file" button

# Open file dialog and select the downloaded file
# TODO: get the file path from notebooklm_gen.py

# Fill in the title

# Fill in the description

# Maybe fill in the episode number?

# Click "Next" button

# Set the publish date radio button to now

# Click the "Publish" button

# Remove the .wav file from the local disk
