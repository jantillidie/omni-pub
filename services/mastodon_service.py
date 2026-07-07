from mastodon import Mastodon

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
    
from config import MASTODON_BASE_URL, MASTODON_ACCESS_TOKEN

def post_with_image(text: str, image_path: str) -> str:
    if not (MASTODON_BASE_URL and MASTODON_ACCESS_TOKEN):
        raise ValueError(
            "Mastodon-Credentials fehlen. Setze MASTODON_HANDLE und "
            "MASTODON_APP_PASSWORD in .env / .envrc."
        )
   
    mastodon = Mastodon(
        access_token=MASTODON_ACCESS_TOKEN,
        api_base_url=MASTODON_BASE_URL
    )

    media = mastodon.media_post(image_path, mime_type="image/png")

    status = mastodon.status_post(text, media_ids=[media["id"]])

    return status["url"]