# 12_YT_TIDY

One uniform name and an Obsidian-ready note for every transcript. Local, no API.

- Script: `12_yt_tidy.py` (`ONE_MENU.bat 12`, or `ONE_MENU.bat 12 --channel "Gary Habermas"`)
- Works on: the channel folders in `yt_subtitles`; writes to `yt_markdown/<Channel>/`
- Menu options it accepts: limit, channel, redo

`Gary Habermas - Chapter 159 - The Historical Jesus - Gary Habermas.md` becomes `Ch 159 - The Historical Jesus.md`
(stored as `Ch 159`, three digits, so the folder sorts in order) with front matter (channel, chapter or number,
published, video_id, url, keywords, tags, source) and the H1 `# Ch 159 · The Historical Jesus`. The rule is in
`engine/ytnames.py`: the channel's name is dropped, Chapter/Episode/Part/Lecture/Session/Lesson become Ch/Ep/Pt/Lec/
Session/Lesson, and a video without a number leads with its publish date when known (`--dates` looks dates up with
yt-dlp), otherwise just the title. Keywords are filled in by 13_YT_CHANNEL_SUMMARY.

Originals stay as they are. `--rename-originals` previews giving them the same names; add `--apply` to do it.

**Watcher:** `python stations/12_YT_TIDY/12_yt_tidy.py --watch` keeps an eye on `yt_subtitles`. When a channel has
new files and nothing new for `--quiet-minutes` (default 5; `.part` files mean still downloading), it runs 07
(SRT/VTT/JSON to .md), this station, then 13 (DeepSeek summary; `--no-summary` skips it) for that channel.
