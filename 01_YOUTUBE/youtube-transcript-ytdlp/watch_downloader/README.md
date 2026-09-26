# YouTube Watch Logger & Downloader

Chrome extension + local Python server. Every YouTube video you open is logged;
a popup asks "Download this video?"; clicking **Download** runs yt-dlp automatically.

## Setup
1. Double-click `start_server.bat` (leave the window open).
2. Chrome → `chrome://extensions` → enable **Developer mode** → **Load unpacked** → choose the `extension` folder.
3. Watch a YouTube video — the prompt appears bottom-right.

## Dashboard / batch download
Open http://127.0.0.1:8765/ — see everything you've watched, then
**Download all not-yet-downloaded** or tick boxes and **Download selected**.

## config.json
| key | meaning |
|---|---|
| `download_dir` | where videos go (`<channel>/<title> [id].mp4`) |
| `format` | yt-dlp format; e.g. `best[height<=360]` for small files, `bestaudio` for audio only |
| `proxies` | list like `["http://user:pass@1.2.3.4:8080", "socks5://127.0.0.1:1080"]` |
| `proxy_mode` | proxies rotate per download; on failure the next proxy is tried |
| `concurrent_downloads` | parallel yt-dlp processes |

Restart the server after editing config. Log lives in `watch_log.db` (SQLite).
Videos already downloaded are skipped via `downloaded_archive.txt`.
