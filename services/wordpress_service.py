import requests
from config import WP_API_URL, WP_USERNAME, WP_PASSWORD


def send_menu_to_wordpress(payload: dict) -> int:
    """
    Sendet ein validiertes WordPressPayload als JSON an die WordPress REST API.

    Args:
        payload: Das als Dict serialisierte WordPressPayload-Objekt
                 (enthält title, status, acf).

    Returns:
        HTTP-Statuscode der Antwort (201 = erfolgreich erstellt).

    Raises:
        requests.HTTPError: Wenn WordPress mit einem Fehler-Status antwortet.
        requests.RequestException: Bei Netzwerk-/Verbindungsfehlern.
    """
    posts_endpoint = f"{WP_API_URL}/wp/v2/weekly_menu"

    response = requests.post(
        posts_endpoint,
        json=payload,
        auth=(WP_USERNAME or "", WP_PASSWORD or ""),
        timeout=30,
    )
    response.raise_for_status()
    return response.status_code
    