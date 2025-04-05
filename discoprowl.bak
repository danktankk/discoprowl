##<--########################################################
##               DiscoProwl - danktankk                    ##
########################################################-->##

import os
import re
import time
import urllib.parse
import requests
import apprise

# Required env var config: (all required variables must be set via compose or environment)
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

# Required configuration parameters
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

# Optional SteamGridDB API key for dynamic images
STEAMGRIDDB_API_KEY = os.getenv("STEAMGRIDDB_API_KEY", "").strip()

# Optional disallowed keywords (case-insensitive)
disallowed_keywords_env = os.getenv("DISALLOWED_KEYWORDS")
if disallowed_keywords_env:
    DISALLOWED_KEYWORDS = [kw.strip().lower() for kw in disallowed_keywords_env.split(",") if kw.strip()]
else:
    DISALLOWED_KEYWORDS = []

# Notification configurations from environment: (At least one must be set)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
APPRISE_URL = os.getenv("APPRISE_URL", "").strip()
PUSHOVER_APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN", "").strip()
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY", "").strip()

if not (DISCORD_WEBHOOK_URL or APPRISE_URL or (PUSHOVER_APP_TOKEN and PUSHOVER_USER_KEY)):
    raise SystemExit(
        "No notification method provided. Please set at least one of DISCORD_WEBHOOK_URL, "
        "APPRISE_URL, or both PUSHOVER_APP_TOKEN and PUSHOVER_USER_KEY."
    )

# Debug prints (remove in production)
# print("Prowlarr URL:", prowlarr_url)
# print("API Key:", API_KEY)
# print("Search Items:", SEARCH_ITEMS)


def is_game(result):
    """
    Determines if a search result is likely a game by checking its category data
    from the Prowlarr API. If any category name contains "pc" or "games" (case-insensitive),
    it is considered a game.

    :param result: A dict representing a search result.
    :return: True if the result is likely a game, otherwise False.
    """
    categories = result.get("categories", [])
    for cat in categories:
        cat_name = cat.get("name", "").lower()
        if "pc" in cat_name or "games" in cat_name:
            return True
    return False


def passes_filters(result, query):
    """
    Returns True if the result meets all filtering criteria:
      - It passes the is_game() check.
      - Its filename does NOT contain any disallowed keywords.
      - Its age is within the MAX_AGE_DAYS cutoff (if numeric).
      - Its filename contains the full query as a whole word.

    :param result: A dict representing a search result.
    :param query: The search query string.
    :return: True if the result passes all filters, otherwise False.
    """
    if not is_game(result):
        return False

    filename = result.get("fileName", "").lower()
    for kw in DISALLOWED_KEYWORDS:
        if kw in filename:
            return False

    age_val = result.get("age", "N/A")
    try:
        age_int = int(age_val)
        if age_int > MAX_AGE_DAYS:
            return False
    except ValueError:
        return False

    # Force full match for the query to prevent most false positives.
    safe_query = re.escape(query.lower().strip())
    if not re.search(rf'\b{safe_query}\b', filename):
        return False

    return True


def get_game_image_url(query):
    """
    Uses the SteamGridDB API's autocomplete endpoint to fetch an image URL for the game
    matching the query. If no API key is provided or no image is found, returns a fallback URL.

    :param query: The search query string.
    :return: URL string for the game image.
    """
    local_asset_path = "assets/no-image2.jpg"
    return local_asset_path

#    fallback_url = "https://raw.githubusercontent.com/danktankk/discoprowl/main/assets/no-image.jpg"

#    if not STEAMGRIDDB_API_KEY:
#        print("No SteamGridDB API key set.")
#        return fallback_url

    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{encoded_query}"
        print(f"Fetching image for query: '{query}'")

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {STEAMGRIDDB_API_KEY}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        print("Autocomplete response:", data)

        if not data.get("data"):
            print(f"No data found for query '{query}' on SteamGridDB.")
            return fallback_url

        game_id = data["data"][0]["id"]
        print(f"Game ID for '{query}' is {game_id}")

        grid_url = f"https://www.steamgriddb.com/api/v2/grids/game/{game_id}"
        grid_response = requests.get(
            grid_url,
            headers={"Authorization": f"Bearer {STEAMGRIDDB_API_KEY}"},
            timeout=10,
        )
        grid_response.raise_for_status()
        grids = grid_response.json().get("data", [])
        print("Grid response:", grids)
        if not grids:
            print("No grid images found for this game.")
            return fallback_url

        return grids[0]["url"]

    except requests.HTTPError as http_err:
        if http_err.response.status_code == 404:
            print(f"SteamGridDB API returned 404 for query '{query}', using fallback image.")
            return fallback_url
        else:
            print(f"SteamGridDB API error: {http_err}")
            return fallback_url
    except Exception as exc:
        print(f"SteamGridDB API error: {exc}")
        return fallback_url


def send_notification(query, results):
    """
    Filters results using passes_filters and sends up to MAX_RESULTS via all configured
    notification services.

    :param query: The search query string.
    :param results: A list of dicts representing search results.
    """
    filtered_results = [res for res in results if passes_filters(res, query)]
    filtered_results = filtered_results[:MAX_RESULTS]

    formatted_query = f"**{query.upper()}**"

    if not filtered_results:
        description = f"Search Results for {formatted_query}: No results met the filter criteria."
    else:
        lines = [f"Search Results for {query.upper()}:"]
        for i, res in enumerate(filtered_results, start=1):
            indexer = res.get("indexer", "N/A")
            seeders = res.get("seeders", "N/A")
            filename = res.get("fileName", "N/A")
            age = res.get("age", "N/A")
            lines.append(
                f"**Result {i}:**\n"
                f"Indexer: `{indexer}`\n"
                f"Seeders: `{seeders}`\n"
                f"Filename: `{filename}`\n"
                f"Age: `{age}`"
            )
        description = "\n".join(lines)

    embed = {
        "title": f"Search Results for {formatted_query}",
        "description": description,
        "color": 0x2ECC71 if filtered_results else 0x000000,
    }

    image_url = get_game_image_url(query)
    if filtered_results and image_url:
        embed["thumbnail"] = {"url": image_url}

    payload = {
        "username": "DiscoBot!",
        "content": "",
        "embeds": [embed],
    }

    if DISCORD_WEBHOOK_URL:
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=30)
            response.raise_for_status()
            print("Notification sent via Discord.")
        except requests.RequestException as err:
            print(f"Error sending Discord notification: {err}")

    if APPRISE_URL:
        try:
            aobj = apprise.Apprise()
            aobj.add(APPRISE_URL)
            aobj.notify(title=f"Search Results for {formatted_query}", body=description)
            print("Notification sent via Apprise.")
        except Exception as err:
            print(f"Error sending Apprise notification: {err}")

    if PUSHOVER_APP_TOKEN and PUSHOVER_USER_KEY:
        pushover_method = os.getenv("PUSHOVER_METHOD", "api").lower()
        if pushover_method == "apprise":
            try:
                aobj = apprise.Apprise()
                pushover_url = f"pushover://{PUSHOVER_USER_KEY}/{PUSHOVER_APP_TOKEN}"
                aobj.add(pushover_url)
                aobj.notify(title=f"Search Results for {formatted_query}", body=description)
                print("Notification sent via Pushover (Apprise).")
            except Exception as err:
                print(f"Error sending Pushover notification via Apprise: {err}")
        else:
            try:
                pushover_payload = {
                    "token": PUSHOVER_APP_TOKEN,
                    "user": PUSHOVER_USER_KEY,
                    "message": description,
                    "title": f"Search Results for {formatted_query}",
                }
                pushover_response = requests.post(
                    "https://api.pushover.net/1/messages.json",
                    data=pushover_payload,
                    timeout=30,
                )
                pushover_response.raise_for_status()
                print("Notification sent via Pushover (Direct API).")
            except Exception as err:
                print(f"Error sending Pushover notification via API: {err}")


def search_item(query):
    """
    Searches Prowlarr for a given query using a GET request.

    :param query: The search query string.
    :return: The JSON response from Prowlarr if successful, or None on error.
    """
    url = f"{prowlarr_url}/api/v1/search"
    params = {
        "query": query,
        "type": "search",
        "indexerIds": [],
    }
    headers = {"X-Api-Key": API_KEY}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as err:
        print(f"Error searching for '{query}': {err}")
        return None


def main():
    """
    Main function that continuously cycles through the search items,
    performs searches, and sends notifications.
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
            print()
        print(
            f"Cycle complete. Waiting for {INTERVAL_HOURS} hours before the next search cycle..."
        )
        time.sleep(INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    main()
