"""
DiscoProwl - danktankk
This script searches Prowlarr, fetches game images from SteamGridDB,
and sends notifications via Discord, Apprise, and Pushover.
"""

import os
import re
import time
import urllib.parse
import requests
import apprise  # pylint: disable=import-error

# Required environment variables
prowlarr_url = os.getenv("PROWLARR_URL")
if not prowlarr_url:
    raise SystemExit("Missing environment variable PROWLARR_URL.")
prowlarr_url = prowlarr_url.strip()
if not prowlarr_url.startswith("https://"):
    prowlarr_url = "https://" + prowlarr_url

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise SystemExit("Missing environment variable API_KEY.")
API_KEY = API_KEY.strip()

search_items_env = os.getenv("SEARCH_ITEMS")
if not search_items_env:
    raise SystemExit("Missing environment variable SEARCH_ITEMS.")
search_items_env = search_items_env.strip()
SEARCH_ITEMS = [item.strip() for item in search_items_env.split(",") if item.strip()]

try:
    INTERVAL_HOURS = float(os.getenv("INTERVAL_HOURS", "12"))
except ValueError:
    INTERVAL_HOURS = 12

try:
    MAX_RESULTS = int(os.getenv("MAX_RESULTS", "3"))
except ValueError:
    MAX_RESULTS = 3

try:
    MAX_AGE_DAYS = int(os.getenv("MAX_AGE_DAYS", "30"))
except ValueError:
    MAX_AGE_DAYS = 30

STEAMGRIDDB_API_KEY = os.getenv("STEAMGRIDDB_API_KEY", "").strip()

disallowed_keywords_env = os.getenv("DISALLOWED_KEYWORDS")
if disallowed_keywords_env:
    DISALLOWED_KEYWORDS = [kw.strip().lower() for kw in disallowed_keywords_env.split(",")
                           if kw.strip()]
else:
    DISALLOWED_KEYWORDS = []

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
APPRISE_URL = os.getenv("APPRISE_URL", "").strip()
PUSHOVER_APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN", "").strip()
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY", "").strip()

if not (DISCORD_WEBHOOK_URL or APPRISE_URL or (PUSHOVER_APP_TOKEN and PUSHOVER_USER_KEY)):
    raise SystemExit(
        "No notification method provided. Set at least one of DISCORD_WEBHOOK_URL, "
        "APPRISE_URL, or both PUSHOVER_APP_TOKEN and PUSHOVER_USER_KEY."
    )

# ---------------- Helper Functions ----------------

def is_game(result):
    """
    Determines if a search result is likely a game by checking its categories.

    :param result: Dict representing a search result.
    :return: True if result appears to be a game.
    """
    for cat in result.get("categories", []):
        name = cat.get("name", "").lower()
        if "pc" in name or "games" in name:
            return True
    return False

def passes_filters(result, query):
    """
    Check if a search result passes all filtering criteria.

    :param result: Dict representing a search result.
    :param query: The search query.
    :return: True if result passes filters.
    """
    if not is_game(result):
        return False
    filename = result.get("fileName", "").lower()
    for kw in DISALLOWED_KEYWORDS:
        if kw in filename:
            return False
    try:
        if int(result.get("age", "N/A")) > MAX_AGE_DAYS:
            return False
    except ValueError:
        return False
    safe_query = re.escape(query.lower().strip())
    return bool(re.search(rf'\b{safe_query}\b', filename))

def fetch_game_id(query):
    """
    Fetch the game ID from SteamGridDB using the autocomplete endpoint.

    :param query: The search query.
    :return: Game ID or None.
    """
    encoded = urllib.parse.quote(query)
    url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{encoded}"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {STEAMGRIDDB_API_KEY}"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("data"):
        return None
    return data["data"][0]["id"]

def fetch_images(game_id):
    """
    Fetch images for a given game ID from SteamGridDB.

    :param game_id: The game ID.
    :return: List of image dictionaries.
    """
    url = f"https://www.steamgriddb.com/api/v2/grids/game/{game_id}"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {STEAMGRIDDB_API_KEY}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("data", [])

def get_game_image_urls(query):
    """
    Get full-size and thumbnail image URLs for a game.
    Returns a tuple (main_image_url, thumbnail_url).

    :param query: The search query.
    :return: Tuple of image URLs.
    """
    fallback_url = "https://raw.githubusercontent.com/danktankk/discoprowl/main/assets/no-image.jpg"
    if not STEAMGRIDDB_API_KEY:
        print("No SteamGridDB API key set.")
        return fallback_url, fallback_url
    try:
        game_id = fetch_game_id(query)
        if game_id is None:
            print(f"No data found for query '{query}' on SteamGridDB.")
            return fallback_url, fallback_url
        print(f"Game ID for '{query}' is {game_id}")
        images = fetch_images(game_id)
        if not images:
            print("No grid images found for this game.")
            return fallback_url, fallback_url
        main_image = images[0]["url"]
        thumbnail_image = images[1]["url"] if len(images) > 1 else fallback_url
        return main_image, thumbnail_image
    except requests.RequestException as req_err:
        print(f"SteamGridDB API request error: {req_err}")
        return fallback_url, fallback_url

def build_embed(query, filtered_results):
    """
    Build the Discord embed and description.

    :param query: The search query.
    :param filtered_results: List of filtered results.
    :return: Tuple (embed, description).
    """
    formatted = f"**{query.upper()}**"
    if not filtered_results:
        desc = f"Search Results for {formatted}: No results met the filter criteria."
    else:
        lines = [f"Search Results for {query.upper()}:"]
        for i, res in enumerate(filtered_results, start=1):
            lines.append(
                f"**Result {i}:**\n"
                f"Indexer: `{res.get('indexer', 'N/A')}`\n"
                f"Seeders: `{res.get('seeders', 'N/A')}`\n"
                f"Filename: `{res.get('fileName', 'N/A')}`\n"
                f"Age: `{res.get('age', 'N/A')}`"
            )
        desc = "\n".join(lines)
    embed = {
        "title": f"Search Results for {formatted}",
        "description": desc,
        "color": 0x2ECC71 if filtered_results else 0x000000,
    }
    main_img, thumb_img = get_game_image_urls(query)
    if filtered_results:
        if main_img:
            embed["image"] = {"url": main_img}
        if thumb_img:
            embed["thumbnail"] = {"url": thumb_img}
    return embed, desc

# ---------------- Notification Functions ----------------

def send_notification(query, results):
    """
    Filter search results and send notifications.

    :param query: The search query.
    :param results: List of search results.
    """
    filtered = [res for res in results if passes_filters(res, query)]
    filtered = filtered[:MAX_RESULTS]
    embed, desc = build_embed(query, filtered)
    payload = {
        "username": "DiscoBot!",
        "content": "",
        "embeds": [embed],
    }
    if DISCORD_WEBHOOK_URL:
        try:
            resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=30)
            resp.raise_for_status()
            print("Notification sent via Discord.")
        except requests.RequestException as err:
            print(f"Error sending Discord notification: {err}")
    if APPRISE_URL:
        try:
            aobj = apprise.Apprise()
            aobj.add(APPRISE_URL)
            aobj.notify(title=f"Search Results for {query.upper()}", body=desc)
            print("Notification sent via Apprise.")
        except Exception as err:  # pylint: disable=broad-exception-caught
            print(f"Error sending Apprise notification: {err}")
    if PUSHOVER_APP_TOKEN and PUSHOVER_USER_KEY:
        pushover_method = os.getenv("PUSHOVER_METHOD", "api").lower()
        if pushover_method == "apprise":
            try:
                aobj = apprise.Apprise()
                pushover_url = f"pushover://{PUSHOVER_USER_KEY}/{PUSHOVER_APP_TOKEN}"
                aobj.add(pushover_url)
                aobj.notify(title=f"Search Results for {query.upper()}", body=desc)
                print("Notification sent via Pushover (Apprise).")
            except Exception as err:  # pylint: disable=broad-exception-caught
                print(f"Error sending Pushover notification via Apprise: {err}")
        else:
            try:
                pushover_payload = {
                    "token": PUSHOVER_APP_TOKEN,
                    "user": PUSHOVER_USER_KEY,
                    "message": desc,
                    "title": f"Search Results for {query.upper()}",
                }
                pr = requests.post(
                    "https://api.pushover.net/1/messages.json",
                    data=pushover_payload,
                    timeout=30,
                )
                pr.raise_for_status()
                print("Notification sent via Pushover (Direct API).")
            except Exception as err:  # pylint: disable=broad-exception-caught
                print(f"Error sending Pushover notification via API: {err}")

def search_item(query):
    """
    Search Prowlarr for a given query.

    :param query: The search query.
    :return: JSON response if successful, else None.
    """
    url = f"{prowlarr_url}/api/v1/search"
    params = {"query": query, "type": "search", "indexerIds": []}
    headers = {"X-Api-Key": API_KEY}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as err:
        print(f"Error searching for '{query}': {err}")
        return None

def main():
    """
    Main function that cycles through search items and sends notifications.
    """
    print(f"Starting search cycle for {len(SEARCH_ITEMS)} items...")
    while True:
        for query in SEARCH_ITEMS:
            print(f"Searching for: {query}")
            results = search_item(query)
            if results is not None:
                print(f"Found {len(results)} results for '{query}'.")
            else:
                print(f"No results returned for '{query}'.")
            send_notification(query, results or [])
            print()  # Blank line between queries
        print(f"Cycle complete. Waiting for {INTERVAL_HOURS} hours before next cycle...")
        time.sleep(INTERVAL_HOURS * 3600)

if __name__ == "__main__":
    main()
