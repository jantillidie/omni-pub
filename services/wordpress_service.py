import requests
from config import WP_API_URL, WP_USERNAME, WP_PASSWORD

def send_menu_to_wordpress(payload: dict):
    posts_endpoint = f"{WP_API_URL}/wp/v2/weekly_menu"
    
    response = requests.post(
        posts_endpoint, 
        json=payload, 
        auth=(WP_USERNAME, WP_PASSWORD)
    )
    
    return response.status_code