# YouTube Capture GUI

Start with:

```bat
START-YT-Transcript-GUI.bat
```

Use the batch file instead of double-clicking `YT-Transcript.ahk`. The batch file launches the script with the installed AutoHotkey v1 Unicode 64-bit executable and avoids wrong-engine problems.

## How It Works

1. Run `START-YT-Transcript-GUI.bat`.
2. Open a YouTube video in Chrome, Edge, Brave, Firefox, Vivaldi, or Opera.
3. Do not type the URL. The watcher scans the active browser tab and shows the URL it found.
4. If it found the right video, choose what to do:
   - `Subtitles`
   - `Audio`
   - `Video`
   - `All`
   - `Not This One`
5. Output goes to:

```text
C:\Users\David\yt_captures
```

Hotkeys:

- `Shift+F4`: detect the current browser tab now.
- `Shift+F5`: reopen the control panel.

Typing or pasting a URL should only be a fallback if active-tab detection fails. The normal workflow is: open YouTube video -> watcher detects URL -> choose action.

The backend is the downloader installed at:

```text
D:\GitHub\yt-bulk-subtitles-downloader
```

The local bridge script is:

```text
yt_capture_url.ps1
```
