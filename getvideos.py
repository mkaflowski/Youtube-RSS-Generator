import googleapiclient.discovery
from googleapiclient.errors import HttpError
from pytube import YouTube
from datetime import datetime as dt
import generator
from apiKey import apiKeyList
import os
import sys
from bs4 import BeautifulSoup

catalog_path = os.path.dirname(sys.argv[0])


def getVideosIds(key, channel_id, title_filter=None, playlist_id=None, limit=5):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=key)

    if playlist_id is None:
        channel_info = getChannelInfo(channel_id, youtube)
        items = getItemsForChannel(channel_id, youtube)
    else:
        channel_info = getPlaylistInfo(playlist_id, youtube)
        items = getItemsForPlaylist(playlist_id, youtube)

    if title_filter is not None:
        items = list(filter(lambda it: title_filter.lower() in it["snippet"]["title"].lower(), items))
    items = items[:limit]
    print(f"total: {len(items)}")


    videos = []

    for item in items:
        # try:
        if playlist_id is None:
            video_id = item["id"]["videoId"]
        else:
            video_id = item["snippet"]["resourceId"]["videoId"]

        title2 = item["snippet"]["title"]
        desc2 = item["snippet"]["description"]
        image2 = item["snippet"]["thumbnails"]["medium"]["url"]

        published_at = item["snippet"]["publishedAt"].replace("T", " ").replace("Z", " ").rstrip()
        date_obj = dt.strptime(published_at, '%Y-%m-%d %H:%M:%S')
        published_at = dt.strftime(date_obj, "%a, %d %b %Y %H:%M:%S +0000")

        url2 = None
        rss_file_data = getRssData(channel_info["id"])
        if rss_file_data is not None:
            url2 = getLinkFromRssFile(video_id, rss_data=rss_file_data)
        print(url2)

        if url2 is None:
            yt = YouTube('http://youtube.com/{0}'.format(video_id))
            stream = yt.streams.filter(res="720p", file_extension='mp4', only_video=False).first()
            if stream is None:
                stream = yt.streams.filter(res="360p", file_extension='mp4', only_video=False).first()
            if stream is None:
                stream = yt.streams.filter(only_audio=True).last()
            if stream is not None:
                url2 = stream.url
            print(url2)

        video = {
            "videoId": video_id,
            "title": title2,
            "desc": desc2,
            "image": image2,
            "published": published_at,
            "url": url2
        }

        videos.append(video)
    # except:
    #     print("Something went wrong  with {0}".format(item))

    generated_catalog_path = catalog_path + "/generated/"
    # Check whether the specified path exists or not
    isExist = os.path.exists(generated_catalog_path)
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(generated_catalog_path)
        print("The new directory is created! " + generated_catalog_path)

    generator.generate(generated_catalog_path + channel_info["id"] + ".rss", channel_info, videos)


def getItemsForChannel(channel_id, youtube):
    request = youtube.search().list(
        part="snippet,id",
        channelId=channel_id,
        maxResults=50,
        type="video",
        order="date"
    )
    response = request.execute()
    items = response["items"]
    return items


def getItemsForPlaylist(playlist_id, youtube):
    request = youtube.playlistItems().list(
        part="snippet,id",
        playlistId=playlist_id,
    )
    response = request.execute()
    items = response["items"]
    return items


def getChannelInfo(channel_id, youtube):
    request = youtube.channels().list(
        part="snippet",
        id=channel_id,
    )
    response = request.execute()
    channel_info = {}
    channel_info["title"] = response["items"][0]["snippet"]["title"]
    channel_info["desc"] = response["items"][0]["snippet"]["description"]
    channel_info["author"] = response["items"][0]["snippet"]["title"]
    channel_info["id"] = response["items"][0]["id"]
    channel_info["link"] = "https://www.youtube.com/channel/" + channel_info["id"]
    channel_info["imgurl"] = response["items"][0]["snippet"]["thumbnails"]["medium"]["url"]
    return channel_info


def getPlaylistInfo(pl_id, youtube):
    request = youtube.playlists().list(
        part="snippet",
        id=pl_id,
    )
    response = request.execute()
    channel_info = {}
    channel_info["title"] = response["items"][0]["snippet"]["title"]
    channel_info["desc"] = response["items"][0]["snippet"]["description"]
    channel_info["author"] = response["items"][0]["snippet"]["channelTitle"]
    channel_info["id"] = response["items"][0]["id"]
    channel_info["link"] = "https://www.youtube.com/playlist?list=" + channel_info["id"]
    channel_info["imgurl"] = response["items"][0]["snippet"]["thumbnails"]["medium"]["url"]
    channel_info["imgurl"] = response["items"][0]["snippet"]["thumbnails"]["medium"]["url"]

    return channel_info


def getRssData(channel_id):
    rss_file = catalog_path + "/generated/" + channel_id + ".rss"
    # Check whether the specified path exists or not
    isExist = os.path.exists(rss_file)
    if not isExist:
        print("RSS file {0} doesn't exist.".format(rss_file))
        return None
    with open(rss_file, 'r') as f:
        data = f.read()
        Bs_data = BeautifulSoup(data, "lxml")
        f.close()
        return Bs_data


def getLinkFromRssFile(guid, rss_data):
    item = rss_data.find("guid", string=guid)
    if item is not None:
        url = item.parent.enclosure.get("url")
        print("{0} - LINK FOUND IN RSS".format(guid))
        return url
    print("GUID not found")
    return None


def disableSSL():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context


# disableSSL()

try:
    getVideosIds(apiKeyList[0], channel_id=None, playlist_id="PLi6mayoXmypQ4iGlGnKWhw0Acy5Wxc4kV")
except HttpError as err:
    print("An exception occurred: {0}".format(err))
    getVideosIds(apiKeyList[1], "UCapiydRNc88rlAYcgzjPYGg", "rozmowa")
