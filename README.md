# ChatGPT to Spotify Podcast

This project automates turning a daily ChatGPT conversation into a podcast
episode and publishing it on Spotify.

The workflow is:

1. **ChatGPT** – fetch the latest message from a specified conversation.
2. **NotebookLM** – generate an audio summary from the text.
3. **Spotify** – upload the audio file as a new episode.

## Requirements

* Python 3.10+
* Google Chrome (used by [nodriver](https://github.com/cscorley/nodriver))
* Accounts for ChatGPT, Google NotebookLM and Spotify

Install Python dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy the example environment file and edit it with your ChatGPT conversation ID:

```bash
cp example.env .env
```

Update `.env`:

```env
conversation_id="YOUR_CONVERSATION_ID"
```

During the first run, browser windows will appear for each service so you can
log in manually. Authentication cookies are then saved for subsequent runs.

## Usage

Run the scheduler, which executes once daily at 05:00 UTC:

```bash
python src/main.py
```

For debugging, each component can also be invoked separately:

```bash
python src/chatgpt_pull.py      # fetch latest ChatGPT message
python src/notebooklm_gen.py    # generate NotebookLM audio
python src/spotify_upload.py    # upload audio to Spotify
```

## ChatGPT Login Troubleshooting

If you encounter a `409` error while logging into ChatGPT, open the ChatGPT
website in a regular browser via Google and sign in before rerunning the
script.

## License

This project is released under the [MIT License](LICENSE).

