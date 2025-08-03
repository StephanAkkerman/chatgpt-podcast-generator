import nodriver

from chatgpt_pull import get_latest_reply
from notebooklm_gen import generate_podcast
from spotify_upload import upload_podcast


def main():
    # 1. Get the chatGPT response
    cid = "6855081e-83e8-8005-81bd-bdd27276805e"  # TODO: move to config

    # nodriver's own helper avoids "event loop closed" issues on Windows
    loop = nodriver.loop()
    loop.run_until_complete(get_latest_reply(cid))

    # 2. Start NotebookLM to generate the audio
    loop.run_until_complete(generate_podcast())

    # 3. Save it as a podcast episode on Spotify
    loop.run_until_complete(upload_podcast())


if __name__ == "__main__":
    # Loop every 24h at 08:00 UTC
    main()
