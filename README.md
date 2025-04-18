<p align="center">
  <img src="https://raw.githubusercontent.com/danktankk/discoprowl/main/assets/logo-circular.png" alt="DiscoProwl Icon" height="100" style="vertical-align: middle;"/>
  <img src="https://raw.githubusercontent.com/danktankk/discoprowl/main/assets/logo-namer.png" alt="DiscoProwl Text" height="65" style="vertical-align: middle; margin-left: 10px;"/>
</p>



---

## What Is DiscoProwl?

Have you ever found yourself watching upcoming latest AAA game title videos and then saw several you MUST have?  Did you then make a list of them and diligently search for these games daily until it released? No?  Me either. I just forgot about it until some random conversation brought these items back into focus.  But by now, there are *other games* that are just around the corner and you have missed time that *could have been spent* happily wasting your life away playing your new game.  That sucks, so I decided to whip up a little 'app-for-that' to help out on the whole "waste your life away" thing.    

**DiscoProwl** is a lightweight Python-powered search assistant for [Prowlarr](https://github.com/Prowlarr/Prowlarr) that was created for a specific need I have.  There is no WebUI for this project currently and doesnt really need one.  Just start the container and then wait for notificaitons after testing with a known release.  It periodically searches your configured indexers for game titles (or anything really) you want, filters out irrelevant junk that you define (Ex: console releases, macOS, old uploads, etc), and notifies you when results match your query.  This is useful when you are waiting on a game to drop and want to get it as soon as possible!  You will be notified and then you decide how to proceed.  In future releases then will be more streamlined.

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
2. Queries Prowlarr's `/api` endpoint
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
    environment:
      PROWLARR_URL: ${PROWLARR_URL}
      API_KEY: ${API_KEY}
      SEARCH_ITEMS: "game 1,game2" 
      MAX_AGE_DAYS: ""      ## ---[ defaults to 30 days ]--- ##
      INTERVAL_HOURS: ""    ## ---[ defaults to 12 hours ]--- ##
      MAX_RESULTS: ""       ## ---[ defaults to 3 ]--- ##
      DISALLOWED_KEYWORDS: "ps4,ps5"
      DISCORD_WEBHOOK_URL: ${DISCORD_WEBHOOK_URL}
      STEAMGRIDDB_API_KEY: ${STEAMGRIDDB_API}
      ## Provide only one of the following notification configurations:
      ## DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/yourhook"
      ## APPRISE_URL: "apprise://yourappriseurl"
      ## PUSHOVER_APP_TOKEN: "yourpushoverapptoken"
      ## PUSHOVER_USER_KEY: "yourpushoveruserkey"
    restart: unless-stopped

Age filtering (e.g., ignore stuff older than 30 days)

Thumbnail artwork via SteamGridDB (optional)

Discord, Apprise, or Pushover notifications

Runs as a Docker container or directly on any system with Python 3.9+.

## Required Environment Variables
Variable	Description
PROWLARR_URL	Your Prowlarr instance URL (https only)
API_KEY	  Prowlarr API key
SEARCH_ITEMS	Comma-separated search terms
INTERVAL_HOURS	(Default: 12) Time between search runs
MAX_RESULTS	(Default: 3) Max results per search term
MAX_AGE_DAYS	(Default: 30) Ignore older torrents
🔔 Notification Options
You must set at least one of these:

## Variable	Description
DISCORD_WEBHOOK_URL	Discord webhook for sending results
APPRISE_URL	        Apprise notification target
PUSHOVER_APP_TOKEN	Pushover App Token
PUSHOVER_USER_KEY	Pushover User Key

## Optional Extras
Variable	Description
STEAMGRIDDB_API_KEY	API key for getting game art (optional)
DISALLOWED_KEYWORDS	Comma-separated words to block (optional)

## How It Works
Takes your SEARCH_ITEMS list and queries them against Prowlarr

Filters out anything that’s too old, not categorized as PC/Games, or contains blacklisted keywords

Sends a rich Discord embed (or other notifications)

Optionally includes game thumbnails via SteamGridDB

Repeats every INTERVAL_HOURS

## Tips
This script does not filter based on just partial keyword matches — it uses whole-word boundary detection.

If no image is found for a game title, it uses a fallback from your repo.

It’s optimized to work in headless environments and logs to stdout for Docker logs -f.

