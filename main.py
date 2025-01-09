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

# Append to the LIVE section (static content)
VIDEOS["LIVE"].append(
    {
        "name": "CNN (US) -- No Geo Restriction",
        "thumb": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/cnn-us.png",
        "video": "https://turnerlive.warnermediacdn.com/hls/live/586495/cnngo/cnn_slate/VIDEO_0_3564000.m3u8",
        "genre": "LIVE",
    }
)

VIDEOS["LIVE"].append(
    {
        "name": "CNN (INTERNATIONAL) -- No Geo Restriction",
        "thumb": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/cnn-us.png",
        "video": "https://turnerlive.warnermediacdn.com/hls/live/586497/cnngo/cnni/VIDEO_0_3564000.m3u8",
        "genre": "LIVE",
    }
)

# Cache page fetches with increased size
@lru_cache(maxsize=100)
def fetch_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return ""  # Return empty content on failure

# Cache video metadata
meta_cache = {}

def get_meta(url):
    if url in meta_cache:
        return meta_cache[url]
    content = fetch_url(url)
    title = re.search(r"<title>(.*?)</title>", content)
    mp4_link = re.search(r"https?://[^\s\"']+\.mp4", content)
    thumb = re.search(r'<meta\s+name="twitter:image"\s+content="([^"]+)"', content)
    meta = [
        mp4_link.group(0) if mp4_link else None,
        title.group(1) if title else None,
        thumb.group(1).split("?")[0] if thumb else None,
    ]
    meta_cache[url] = meta
    return meta

# List and populate videos
def list_videos(VIDEOS):
    url = "https://edition.cnn.com/world"
    content = fetch_url(url)
    if not content:
        return
    links = list(
        {
            match if match.startswith("http") else f"https://www.cnn.com{match}"
            for match in re.findall(r"[^\"'\s]+/video/[^\"'\s]+", content)
        }
    )[:10]  # Limit to the first 10 links for speed
    for link in links:
        item = get_meta(link)
        if item[0]:  # Only add if a valid video link exists
            VIDEOS["VIDEOS"].append(
                {
                    "name": item[1].replace(" | CNN", "") if item[1] else "Unknown Title",
                    "thumb": item[2],
                    "video": item[0],
                    "genre": "VIDEOS",
                }
            )

# Populate the VIDEOS dictionary
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

def list_videos_kodi(category):
    """
    Lists videos for the specified category in the Kodi interface.
    Special handling for the 'LIVE' category to avoid unnecessary processing.
    """
    xbmcplugin.setPluginCategory(int(sys.argv[1]), category)
    xbmcplugin.setContent(int(sys.argv[1]), "videos")

    if category == "LIVE":
        # Handle the LIVE category explicitly to avoid unnecessary operations
        for video in VIDEOS["LIVE"]:
            list_item = xbmcgui.ListItem(label=video["name"])
            list_item.setInfo(
                "video",
                {"title": video["name"], "genre": "LIVE", "mediatype": "video"},
            )
            list_item.setArt(
                {"thumb": video["thumb"], "icon": video["thumb"], "fanart": video["thumb"]}
            )
            list_item.setProperty("IsPlayable", "true")
            url = get_url(action="play", video=video["video"])
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, False)
    else:
        # Handle other categories dynamically
        for video in VIDEOS[category]:
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

    # End of directory with caching to disk enabled for better performance
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
            raise ValueError("Invalid paramstring: {0}!".format(paramstring))
    else:
        list_categories()

if __name__ == "__main__":
    router(sys.argv[2][1:])
