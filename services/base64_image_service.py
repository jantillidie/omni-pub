import base64


def encode_local_image(image_path: str) -> str:
    """
    Liest ein Bild von der Festplatte und gibt es als Base64-String zurück.

    Args:
        image_path: Pfad zur Bilddatei (z.B.: "tests/bild.jpg").

    Returns:
        Base64-kodierter String des Bildes (ohne data:-Prefix).
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")