import argparse
import asyncio
import datetime as dt
import logging
import sys
import zoneinfo

from chatgpt_pull import get_latest_reply
from notebooklm_gen import generate_podcast
from spotify_upload import upload_podcast

UTC = zoneinfo.ZoneInfo("UTC")
LOGF = "daily.log"


# ───────────────────────── helpers ──────────────────────────
def seconds_until_5utc() -> float:
    now = dt.datetime.now(UTC)
    target = now.replace(hour=5, minute=0, second=0, microsecond=0)
    if target <= now:
        target += dt.timedelta(days=1)
    return (target - now).total_seconds()


# ───────── make the pipeline async ─────────
async def run_once() -> None:
    md = await get_latest_reply()
    title, summary, wav = await generate_podcast(md)
    await upload_podcast(title, summary, wav)


# ───────── daily scheduler ─────────
async def scheduler() -> None:
    while True:
        sleep_for = seconds_until_5utc()
        logging.info("Sleeping %.1f s until next 05:00 UTC run", sleep_for)
        await asyncio.sleep(sleep_for)
        try:
            await run_once()  # ← await, no nested loop
            logging.info("Daily run finished")
        except Exception:
            logging.exception("Daily run failed")


# ───────────────────────── main ────────────────────────────
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
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(LOGF, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    if args.now:  # one-off run
        asyncio.run(run_once())
    else:  # scheduled loop
        asyncio.run(scheduler())


if __name__ == "__main__":
    main()
