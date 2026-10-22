"""Minimal adapted yt-dlp subtitle fields; see YT_DLP_SOURCE.md and Unlicense."""
PLAYER_API = 'https://api.bilibili.com/x/player/wbi/v2'


def subtitle_tracks(video_info):
    data = video_info.get('data') or {}
    return data.get('need_login_subtitle', False), (data.get('subtitle') or {}).get('subtitles') or []


def subtitle_fields(s):
    return s.get('lan'), s.get('subtitle_url')
