import nodriver

from chatgpt_pull import get_latest_reply
from notebooklm_gen import generate_podcast
from spotify_upload import upload_podcast


def main():
    # nodriver's own helper avoids "event loop closed" issues on Windows
    loop = nodriver.loop()
    md = loop.run_until_complete(get_latest_reply())

    # 2. Start NotebookLM to generate the audio
    title, summary, wav_path = loop.run_until_complete(generate_podcast(md))

    # 3. Save it as a podcast episode on Spotify
    loop.run_until_complete(upload_podcast(title, summary, wav_path))


if __name__ == "__main__":
    # TODO: Loop every 24h at 05:00 UTC
    # TODO: add logging
    main()
