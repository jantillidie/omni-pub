from atproto import Client, models

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
    
from config import BLUESKY_HANDLE, BLUESKY_APP_PASSWORD

def post_with_image(text: str, image_path: str, alt_text: str = "Tagesmenü Flyer") -> str:
    if not (BLUESKY_HANDLE and BLUESKY_APP_PASSWORD):
        raise ValueError(
            "Bluesky-Credentials fehlen. Setze BLUESKY_HANDLE und "
            "BLUESKY_APP_PASSWORD in .env / .envrc."
        )
    client = Client()
    client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)

    image_bytes = Path(image_path).read_bytes()

    upload = client.upload_blob(image_bytes)

    embed = models.AppBskyEmbedImages.Main(
        images=[models.AppBskyEmbedImages.Image(alt=alt_text, image=upload.blob)]
    )

    post = client.send_post(text=text, embed=embed)

    return post.uri