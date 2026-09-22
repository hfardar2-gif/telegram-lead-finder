# Telegram Lead Finder — Phase 1

A Windows-friendly, privacy-conscious tool for discovering public Telegram groups by keyword, analyzing accessible public messages, identifying active public participants, scoring activity, and exporting results. Phase 1 intentionally contains **no bulk messaging, invites, member adding, private-group scraping, multi-account rotation, or rate-limit bypass**.

## Features

- Public group/supergroup/channel discovery using Telegram's supported search API
- Public-message scanning with message-count and day limits
- Deduplicated users and per-group activity in SQLite
- Activity levels: Low (1), Medium (2–5), High (6+), plus recency bonus
- Admin-only Telegram bot with dashboard, discovery, groups, scanning, statistics, exports, and backup
- CSV/XLSX exports excluding bots/deleted accounts from leads
- FloodWait-safe jobs that pause without bypassing Telegram limits
- Local Telethon session and secret-safe configuration

## Architecture

`app/telegram_client` handles Telegram discovery/scanning; `app/database` owns persistence; `app/services` contains scoring/export/backup; `app/bot` is the admin UI. SQLite access is isolated in a repository layer so it can later be replaced by PostgreSQL.

## Installation (Windows 10/11)

1. Install Python 3.12+ and select **Add Python to PATH**.
2. Extract the ZIP.
3. Run `setup.bat`.
4. Run `.venv\Scripts\python -m app.setup_wizard` or edit `.env` locally.
5. Run `start.bat`.

Manual setup:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m app.setup_wizard
python -m app.main
```

## Telegram API Setup

Visit `https://my.telegram.org`, sign in with your Telegram phone number, open **API development tools**, and create an app:

- App title: `Telegram Lead Finder`
- Short name: `telegramleadfinder`
- Platform: `Desktop`
- Description: `Personal Telegram public group discovery and activity analysis tool`

Copy `api_id` and `api_hash` only into local `.env`. Never send them in chat or commit them.

## BotFather Setup

Open the verified `@BotFather`, send `/newbot`, use `Telegram Lead Finder`, then try `TelegramLeadFinderBot`. Alternatives: `TelegramLeadFinderAdminBot`, `TLFAdminBot`, or `PublicGroupLeadFinderBot`. Put the token only in `.env` as `BOT_TOKEN`.

## Environment Variables

| Name | Purpose |
|---|---|
| `API_ID`, `API_HASH` | Telegram user-client credentials |
| `BOT_TOKEN` | Admin bot token |
| `ADMIN_TELEGRAM_ID` | Only account allowed to administer the bot |
| `DATABASE_PATH` | SQLite path |
| `SESSION_PATH` | Telethon session path (without extension) |
| `AUTO_BACKUP_HOURS` | Automatic backup interval; use `0` to disable |

The setup wizard masks `API_HASH` and `BOT_TOKEN`. To obtain your admin ID safely, first save `BOT_TOKEN`, run `python -m app.admin_id_helper`, and send `/start` to your new bot. The helper prints and replies with your public Telegram User ID, then stops. Save that number as `ADMIN_TELEGRAM_ID`. The normal admin bot rejects every management command from other IDs.

## First Login

At first start, Telethon asks in the local console for phone number, login code, and (when enabled) 2FA password. Telegram creates a local `.session` file. It is ignored by Git and is not included in releases.

## Running and Using

Send `/start` to your admin bot. Use **Search Groups**, provide a keyword, then open **Groups** and choose **Scan**. The default is the last 500 messages and 30 days; select 100/500/1000/5000 messages and 7/30/90 days under **Settings**. If both exist, scanning stops at whichever limit is reached first.

Discovery may also store broadcast channels as sources, but scanning is intended for groups/discussion groups where authors are publicly visible. Telegram may omit descriptions, member counts, senders, or search results; the app treats those fields as optional.

## Export and Backup

Use **Export** for all or active-only CSV/XLSX. Active-only means Medium/High and always excludes bots/deleted accounts. Use **Backup** for a consistent SQLite snapshot in `data/backups/` and delivery through the admin bot.

## Troubleshooting

- `Missing API_ID...`: run `python -m app.setup_wizard`.
- `FloodWait`: wait for the stated time, then retry. The app never bypasses limits.
- `PRIVATE`/`ACCESS_DENIED`: the current account cannot read that source.
- `ADMIN_REQUIRED`: Telegram requires privileges for that action/source.
- No users: channels may hide authors or have no accessible discussion messages.
- Bot silent: confirm token, admin ID, and that only one polling instance is running.

Logs are written to `logs/app.log`; tokens, API hash, phone, code, password, and session data are never intentionally logged.

## Telegram and Security Limitations

Telegram search is not a complete global index and results depend on account, region, query, and server behavior. The API does not guarantee full member lists or historical access. This project identifies users only from accessible public messages and stores no phone numbers. Use it lawfully and comply with Telegram Terms, privacy law, consent/marketing requirements, and data-retention obligations applicable to you.

## Tests

```powershell
pytest -q
```

Tests cover syntax/imports through collection, schema creation, repository upserts, batch inserts, deduplication, scoring, CSV/XLSX output, backup, authorization, and missing-config behavior. Live Telegram discovery/login requires your credentials and is deliberately not exercised by automated tests.
