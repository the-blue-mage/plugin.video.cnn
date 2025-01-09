# -*- coding: utf-8 -*-
import sys
from urllib.parse import urlencode, parse_qsl
import re
import requests
from functools import lru_cache
import xbmcgui
import xbmcplugin

# Initialize VIDEOS dictionary as None
VIDEOS = None

# Cache page fetches with increased size
@lru_cache(maxsize=20)
def fetch_url(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return ""  # Return empty content on failure

# Cache video metadata
@lru_cache(maxsize=20)
def get_meta(url):
    content = fetch_url(url)
    title = re.search(r"<title>(.*?)</title>", content)
    mp4_link = re.search(r"https?://[^\s\"']+\.mp4", content)
    thumb = re.search(r'<meta\s+name="twitter:image"\s+content="([^"]+)"', content)
    return [
        mp4_link.group(0) if mp4_link else None,
        title.group(1) if title else "Unknown Title",
        thumb.group(1).split("?")[0] if thumb else None,
    ]

def generate_videos():
    """
    Generates the VIDEOS dictionary once and returns it.
    """
    videos = {"LIVE": [], "WEB VIDEOS": []}
    
    # Append to the LIVE section (static content)
    videos["LIVE"].extend([
        {
            "name": "CNN (US) -- No Geo Restriction",
            "thumb": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/cnn-us.png",
            "video": "https://turnerlive.warnermediacdn.com/hls/live/586495/cnngo/cnn_slate/VIDEO_0_3564000.m3u8",
            "genre": "LIVE",
        },
        {
            "name": "CNN (INTERNATIONAL) -- No Geo Restriction",
            "thumb": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/cnn-us.png",
            "video": "https://turnerlive.warnermediacdn.com/hls/live/586497/cnngo/cnni/VIDEO_0_3564000.m3u8",
            "genre": "LIVE",
        }
    ])

    # Fetch WEB VIDEOS
    url = "https://edition.cnn.com/world"
    content = fetch_url(url)
    if content:
        links = list(
            {
                match if match.startswith("http") else f"https://www.cnn.com{match}"
                for match in re.findall(r"[^\"'\s]+/video/[^\"'\s]+", content)
            }
        )[:10]  # Limit to the first 10 links for speed
        for link in links:
            item = get_meta(link)
            if item[0]:  # Only add if a valid video link exists
                videos["WEB VIDEOS"].append(
                    {
                        "name": item[1],
                        "thumb": item[2],
                        "video": item[0],
                        "genre": "WEB VIDEOS",
                    }
                )
    return videos

def get_videos():
    """
    Returns the static VIDEOS dictionary.
    If VIDEOS is not initialized, it generates it first.
    """
    global VIDEOS
    if VIDEOS is None:
        VIDEOS = generate_videos()
    return VIDEOS

# Kodi plugin functions
def get_url(**kwargs):
    return "{0}?{1}".format(sys.argv[0], urlencode(kwargs))

def get_categories():
    return get_videos().keys()

def get_web_videos(category):
    return get_videos()[category]

def list_categories():
    xbmcplugin.setPluginCategory(int(sys.argv[1]), "My Video Collection")
    xbmcplugin.setContent(int(sys.argv[1]), "videos")
    for category in get_categories():
        videos = get_videos()[category]
        list_item = xbmcgui.ListItem(label=category)
        list_item.setArt({"thumb": videos[0]["thumb"], "icon": videos[0]["thumb"], "fanart": videos[0]["thumb"]})
        list_item.setInfo("video", {"title": category, "genre": category, "mediatype": "video"})
        url = get_url(action="listing", category=category)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, True)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def list_videos_kodi(category):
    xbmcplugin.setPluginCategory(int(sys.argv[1]), category)
    xbmcplugin.setContent(int(sys.argv[1]), "videos")
    videos = get_videos()[category]
    for video in videos:
        list_item = xbmcgui.ListItem(label=video["name"])
        list_item.setInfo("video", {"title": video["name"], "genre": video["genre"], "mediatype": "video"})
        list_item.setArt({"thumb": video["thumb"], "icon": video["thumb"], "fanart": video["thumb"]})
        list_item.setProperty("IsPlayable", "true")
        url = get_url(action="play", video=video["video"])
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, False)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)

def play_video(path):
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=play_item)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params["action"] == "listing":
            list_videos_kodi(params["category"])
        elif params["action"] == "play":
            play_video(params["video"])
        else:
            raise ValueError(f"Invalid paramstring: {paramstring}!")
    else:
        list_categories()

if __name__ == "__main__":
    router(sys.argv[2][1:])
