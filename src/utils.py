import nodriver


async def start_browser(headless: bool, profile_dir: str) -> nodriver.Browser:
    """Launch nodriver with our persistent profile."""
    return await nodriver.start(
        headless=headless,
        no_sandbox=True,
        user_data_dir=profile_dir,
        browser_args=[
            "--disable-dev-shm-usage",
            "--disable-features=ChromeWhatsNewUI",
        ],
    )
