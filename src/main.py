import argparse
import asyncio
import datetime
import logging
import zoneinfo

import nodriver

from chatgpt_pull import get_latest_reply
from notebooklm_gen import generate_podcast
from spotify_upload import upload_podcast

UTC = zoneinfo.ZoneInfo("UTC")
LOGF = "daily.log"


def seconds_until_5utc() -> float:
    """Return how many seconds until the next 05:00 UTC."""
    now = datetime.datetime.now(UTC)
    target = now.replace(hour=5, minute=0, second=0, microsecond=0)
    if target <= now:  # already past 05:00 today
        target += datetime.timedelta(days=1)
    return (target - now).total_seconds()


def run_once():
    # nodriver's own helper avoids "event loop closed" issues on Windows
    loop = nodriver.loop()
    md = loop.run_until_complete(get_latest_reply())

    # 2. Start NotebookLM to generate the audio
    title, summary, wav_path = loop.run_until_complete(generate_podcast(md))

    # 3. Save it as a podcast episode on Spotify
    loop.run_until_complete(upload_podcast(title, summary, wav_path))


async def scheduler():
    while True:
        sleep_for = seconds_until_5utc()
        logging.info("Sleeping %.1f s until next 05:00 UTC run", sleep_for)
        await asyncio.sleep(sleep_for)
        try:
            run_once()
            logging.info("Daily run finished")
        except Exception:
            logging.exception("Daily run failed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate & publish the MarketMind Daily podcast"
    )
    parser.add_argument(
        "-N",
        "--now",
        action="store_true",
        help="Run immediately once and exit (skip the daily schedule)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        filename=LOGF,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    if args.now:  # instant single run
        logging.info("Running single-on-demand job via --now")
        run_once()
    else:  # regular daily loop
        asyncio.run(scheduler())


if __name__ == "__main__":
    main()
