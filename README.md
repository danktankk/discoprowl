<p align="center">
  <img src="https://raw.githubusercontent.com/danktankk/discoprowl/main/assets/logo-circular.png" alt="DiscoProwl Icon" height="100" style="vertical-align: middle;"/>
  <img src="https://raw.githubusercontent.com/danktankk/discoprowl/main/assets/logo-namer.png" alt="DiscoProwl Text" height="65" style="vertical-align: middle; margin-left: 10px;"/>
</p>



---

## What Is DiscoProwl?

**DiscoProwl** is a lightweight Python-powered search assistant for [Prowlarr](https://github.com/Prowlarr/Prowlarr). It periodically searches your configured indexers for game titles you care about, filters out irrelevant junk (console releases, macOS, old uploads), and notifies you when results match your exact query.  This is useful when you are waiting on a game to drop and want to get it as soon as possible!  You will be notified and then you decide how to proceed, for now...

💬 **Notifications** are delivered with choice of the following for the moment:
- Discord webhook (rich embed)
- [Apprise](https://github.com/caronc/apprise) services
- Pushover (mobile push)

It can even pull **box art from SteamGridDB** if you provide an API key — optional, but schmexy!

---

## Required Environment Variables

| Variable           | Description                                      |
|--------------------|--------------------------------------------------|
| `PROWLARR_URL`     | URL to your Prowlarr instance (`https://...`)    |
| `API_KEY`          | Your Prowlarr API key                             |
| `SEARCH_ITEMS`     | Comma-separated list of search terms              |
| `INTERVAL_HOURS`   | Search interval in hours (default: `12`)          |
| `MAX_RESULTS`      | Max results per game to report (default: `3`)    |
| `MAX_AGE_DAYS`     | Ignore results older than this (default: `30`)   |

---

## 🔔 Notification Options

**You must configure at least one of these:**

| Variable                | Description                                 |
|-------------------------|---------------------------------------------|
| `DISCORD_WEBHOOK_URL`   | Discord webhook URL                          |
| `APPRISE_URL`           | Apprise-compatible URL (e.g., Telegram, etc) |
| `PUSHOVER_APP_TOKEN`    | Pushover App Token                           |
| `PUSHOVER_USER_KEY`     | Pushover User Key                            |

---

## Optional Extras

| Variable                | Description                                                      |
|-------------------------|------------------------------------------------------------------|
| `STEAMGRIDDB_API_KEY`   | API key for pulling box art from [SteamGridDB](https://www.steamgriddb.com/) |
| `DISALLOWED_KEYWORDS`   | Comma-separated words to exclude (e.g. `ps5,xbox,macos`)         |

---

## How It Works

1. Reads your search keywords from `SEARCH_ITEMS`
2. Queries Prowlarr's `/api/v1/search` endpoint
3. Filters results using:
   - ✅ Category: must include `games` or `pc`
   - ✅ Filename must include the **full search term** as a whole word
   - ❌ Disallowed terms like `ps5`, `macos`, etc.
   - ⏳ Age must be below `MAX_AGE_DAYS`
4. Sends notifications through all enabled channels
5. Includes box art from SteamGridDB (if enabled)
6. Sleeps for `INTERVAL_HOURS`, then repeats

---

## 🐳 Docker Compose Example

```yaml
services:
  discoprowl:
    image: danktankk/discoprowl:latest
    container_name: discoprowl
    environment:
      PROWLARR_URL: "https://prowlarr.local"
      API_KEY: "your_prowlarr_api_key"
      SEARCH_ITEMS: "doom,borderlands 3,subnautica 2"
      INTERVAL_HOURS: 12
      MAX_RESULTS: 3
      MAX_AGE_DAYS: 30
      DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/yourwebhook"
      STEAMGRIDDB_API_KEY: "optional_api_key"
      DISALLOWED_KEYWORDS: "ps4,ps5,xbox,macos"


Age filtering (e.g., ignore stuff older than 30 days)

Thumbnail artwork via SteamGridDB (optional)

Discord, Apprise, or Pushover notifications

Runs as a Docker container or directly on any system with Python 3.9+.

## Required Environment Variables
Variable	Description
PROWLARR_URL	Your Prowlarr instance URL (https only)
API_KEY	Prowlarr API key
SEARCH_ITEMS	Comma-separated search terms
INTERVAL_HOURS	(Default: 2) Time between search runs
MAX_RESULTS	(Default: 5) Max results per search term
MAX_AGE_DAYS	(Default: 30) Ignore older torrents
🔔 Notification Options
You must set at least one of these:

### Variable	Description
DISCORD_WEBHOOK_URL	Discord webhook for sending results
APPRISE_URL	Apprise notification target
PUSHOVER_APP_TOKEN	Pushover App Token
PUSHOVER_USER_KEY	Pushover User Key
### Optional Extras
Variable	Description
STEAMGRIDDB_API_KEY	API key for getting game art (optional)
DISALLOWED_KEYWORDS	Comma-separated words to block (optional)
### How It Works
Takes your SEARCH_ITEMS list and queries them against Prowlarr

Filters out anything that’s too old, not categorized as PC/Games, or contains blacklisted keywords

Sends a rich Discord embed (or other notifications)

Optionally includes game thumbnails via SteamGridDB

Repeats every INTERVAL_HOURS

### Docker Quick Start
yaml
Copy
Edit
version: "3"
services:
  discoprowl:
    image: danktankk/discoprowl:latest
    environment:
      PROWLARR_URL: https://your-prowlarr.url
      API_KEY: your_api_key
      SEARCH_ITEMS: doom,borderlands 3,fable,subnautica 2
      INTERVAL_HOURS: 2
      MAX_RESULTS: 5
      MAX_AGE_DAYS: 30
      DISCORD_WEBHOOK_URL: https://discord.com/api/webhooks/yourwebhook
      STEAMGRIDDB_API_KEY: your_optional_key
🧠 Tips
This script does not filter based on just partial keyword matches — it uses whole-word boundary detection.

If no image is found for a game title, it uses a fallback from your repo.

It’s optimized to work in headless environments and logs to stdout for Docker logs -f.

