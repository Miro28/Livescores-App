# VDM Score

A modern football livescore desktop app, rebuilt with CustomTkinter.

![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-MIT-green)

## Features

- ⚡ **Live matches** with auto-refresh (30s)
- 📅 **Match listings by date** — today, tomorrow, yesterday, or any custom date
- 📊 **Match details** — visual stat-bar comparisons and starting lineups
- 🔍 **Real-time search** across teams, leagues, and countries
- 🚀 **Threaded API calls** — UI never freezes
- 💾 **In-memory caching** — instant re-clicks within TTL
- 🎨 **Modern dark theme** with consistent components
- 🛡 **Error handling** with retry buttons everywhere

## Project structure

```
vdm_score/
├── main.py                # entry point — run this
├── config.py              # API key + TTL settings
├── theme.py               # color palette
├── api/
│   ├── __init__.py
│   ├── cache.py           # in-memory TTL cache
│   └── client.py          # HTTP calls + threading helper
├── ui/
│   ├── __init__.py
│   ├── app.py             # main VDMScoreApp class
│   ├── components.py      # StatBar, MatchCard widgets
│   └── calendar_popup.py  # themed date picker
├── requirements.txt
├── .api_key.example       # copy to .api_key and put your key inside
├── .gitignore
└── README.md
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your API key

You have **three options** (in priority order):

**Option A — Environment variable (recommended for production):**
```bash
export RAPIDAPI_KEY="your-key-here"     # macOS / Linux
setx RAPIDAPI_KEY "your-key-here"       # Windows
```

**Option B — Local `.api_key` file:**
```bash
cp .api_key.example .api_key
# Then edit .api_key and replace the placeholder with your real key
```

**Option C — Edit `config.py`:**
Open `config.py` and change the `API_KEY` value directly.

> ℹ️ Get a key at [RapidAPI: livescore6](https://rapidapi.com/apidojo/api/livescore6/).
> The repo ships with a default key for convenience but you should replace it with your own.

### 3. Run

```bash
python main.py
```

## How the modules talk

```
main.py
   ↓
ui.app.VDMScoreApp
   ↓ (uses)
   ├── ui.components       (StatBar, MatchCard)
   ├── ui.calendar_popup   (CalendarPopup)
   ├── api                 (fetch_*, cache, run_async)
   └── theme               (COLORS)
            ↓
       config.py            (API key, URLs, TTLs)
```

- All API calls go through `api.client._api_get` so caching and error handling live in one place.
- `run_async(root, worker, on_done)` runs `worker()` in a background thread and dispatches the result back to the Tk main loop via `root.after(0, ...)` — that's how the UI stays responsive.
- The cache is module-global (`api.cache.cache`), so any module that needs to invalidate a key just calls `cache.invalidate("...")`.

## Cache TTLs

| Data type | TTL | Why |
|---|---|---|
| Live matches | 30s | Fast updates without slamming the API |
| Matches by date | 2 min | Mostly stable within a session |
| Statistics / lineups | 5 min | Rarely change once a match is in progress |

You can tune these in `config.py`.

## Troubleshooting

**`ModuleNotFoundError: No module named 'customtkinter'`**
→ Run `pip install -r requirements.txt`.

**`HTTP 401` or `HTTP 403` errors**
→ Your API key is missing, expired, or rate-limited. Re-check `config.py` / `.api_key` / the env var.

**Auto-refresh doesn't work**
→ It's only active on the Live Matches view. Toggle the button in the top bar.

**App feels sluggish on first load**
→ First fetch hits the API; subsequent clicks within the TTL are served from the cache.

## License

MIT — do whatever you want with it.
