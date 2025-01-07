# -*- coding: utf-8 -*-
import sys
from urllib.parse import urlencode, parse_qsl
import re
import requests
from functools import lru_cache
import xbmcgui
import xbmcplugin

# Initial VIDEOS dictionary
VIDEOS = {"LIVE": [], "VIDEOS": []}

# Append to the LIVE section
VIDEOS["LIVE"].append(
    {
        "name": "CNN GO",
        "thumb": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/cnn-us.png",
        "video": "https://turnerlive.warnermediacdn.com/hls/live/586495/cnngo/cnn_slate/VIDEO_0_3564000.m3u8",
        "genre": "LIVE",
    }
)

VIDEOS["LIVE"].append(
    {
        "name": "CNN INTERNATIONAL",
        "thumb": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/cnn-us.png",
        "video": "https://turnerlive.warnermediacdn.com/hls/live/586497/cnngo/cnni/VIDEO_0_3564000.m3u8",
        "genre": "LIVE",
    }
)

# Cache to avoid redundant requests
@lru_cache(maxsize=50)
def fetch_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    return requests.get(url, headers=headers).text

# Scrape video data
def get_meta(url):
    content = fetch_url(url)
    title = re.search(r"<title>(.*?)</title>", content)
    mp4_link = re.search(r"https?://[^\s\"']+\.mp4", content)
    thumb = re.search(r'<meta\s+name="twitter:image"\s+content="([^"]+)"', content)
    return [
        mp4_link.group(0) if mp4_link else None,
        title.group(1) if title else None,
        thumb.group(1).split("?")[0] if thumb else None,
    ]

# List videos
def list_videos(VIDEOS):
    url = "https://edition.cnn.com/world"
    content = fetch_url(url)
    links = list(
        {
            match if match.startswith("http") else f"https://www.cnn.com{match}"
            for match in re.findall(r"[^\"'\s]+/video/[^\"'\s]+", content)
        }
    )[:10]  # Limit to the first 10 links for speed
    for url in links:
        item = get_meta(url)
        if item[0]:  # Only add if a valid video link exists
            VIDEOS["VIDEOS"].append(
                {
                    "name": item[1].replace(" | CNN", "") if item[1] else "Unknown Title",
                    "thumb": item[2],
                    "video": item[0],
                    "genre": "VIDEOS",
                }
            )

list_videos(VIDEOS)

# Kodi plugin functions
def get_url(**kwargs):
    return "{0}?{1}".format(sys.argv[0], urlencode(kwargs))

def get_categories():
    return VIDEOS.keys()

def get_videos(category):
    return VIDEOS[category]

def list_categories():
    xbmcplugin.setPluginCategory(int(sys.argv[1]), "My Video Collection")
    xbmcplugin.setContent(int(sys.argv[1]), "videos")
    for category in get_categories():
        list_item = xbmcgui.ListItem(label=category)
        list_item.setArt(
            {
                "thumb": VIDEOS[category][0]["thumb"],
                "icon": VIDEOS[category][0]["thumb"],
                "fanart": VIDEOS[category][0]["thumb"],
            }
        )
        list_item.setInfo(
            "video", {"title": category, "genre": category, "mediatype": "video"}
        )
        url = get_url(action="listing", category=category)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, True)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def list_videos(category):
    xbmcplugin.setPluginCategory(int(sys.argv[1]), category)
    xbmcplugin.setContent(int(sys.argv[1]), "videos")
    for video in get_videos(category):
        list_item = xbmcgui.ListItem(label=video["name"])
        list_item.setInfo(
            "video",
            {"title": video["name"], "genre": video["genre"], "mediatype": "video"},
        )
        list_item.setArt(
            {"thumb": video["thumb"], "icon": video["thumb"], "fanart": video["thumb"]}
        )
        list_item.setProperty("IsPlayable", "true")
        url = get_url(action="play", video=video["video"])
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, False)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def play_video(path):
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=play_item)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params["action"] == "listing":
            list_videos(params["category"])
        elif params["action"] == "play":
            play_video(params["video"])
        else:
            raise ValueError("Invalid paramstring: {0}!".format(paramstring))
    else:
        list_categories()

if __name__ == "__main__":
    router(sys.argv[2][1:])
