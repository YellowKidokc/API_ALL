# Python Clean Library

Double-click **CLEAN_LIBRARY.bat**. It:

1. **Sorts** any loose transcripts in `..\subtitles\` into per-channel folders
   (`sort_by_channel.py` — asks YouTube which channel each Video ID belongs to).
2. **Cleans** every new or changed transcript into a readable Obsidian note in
   `..\obsidian_transcripts\<Channel>\` (`clean_library.py`). Files already
   cleaned are skipped in about a second, so run it as often as you like.
3. Optionally **zips the originals** of fully cleaned channels into
   `..\_archive_zips\<Channel>__ORIGINAL-raw-transcripts__<date>.zip`.
   Originals are never deleted.

Everything runs locally in Python. No API calls except the channel-name
lookup in step 1.

## Punctuation (optional)

Auto-generated YouTube captions have no punctuation. If the `punctuators`
package is installed, the .bat switches on a local punctuation +
capitalisation model automatically (downloads ~210 MB once):

    pip install punctuators

## Files

| File | What it does |
|---|---|
| `CLEAN_LIBRARY.bat` | the button — runs steps 1-3 |
| `sort_by_channel.py` | loose files -> channel folders |
| `clean_library.py` | transcripts -> Obsidian notes, skip list, zips |
| `transcript_polish.py` | shared parsing/paragraph code (copy of the one next to the downloader) |

To point it at a different library, edit the three `set` lines at the top of
the .bat.
