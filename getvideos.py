import os
import sys
from datetime import datetime as dt
from urllib import parse
from urllib.parse import urlparse
import random

import googleapiclient.discovery
from bs4 import BeautifulSoup
from googleapiclient.errors import HttpError
from pytube import YouTube

import generator
from apiKey import apiKeyList

catalog_path = os.path.dirname(sys.argv[0])


def getVideosIds(key, channel_id, playlist_id=None, title_filter=None, limit=100):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=key)

    if playlist_id is None:
        channel_info = getChannelInfo(channel_id, youtube)
        items = getItemsForChannel(channel_id, youtube)
    else:
        channel_info = getPlaylistInfo(playlist_id, youtube)
        items = getItemsForPlaylist(playlist_id, youtube)

    print("GENERATING: " + channel_info["title"] + " - " + channel_info["link"])

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
        maxResults=100,
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
        maxResults=100,
    )
    response = request.execute()
    items = response["items"]
    print(len(items))
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

def loadLinkToGenerate():
    print("Reading list.txt file: ")
    list = []
    f = open(catalog_path + "/list.txt", "r")
    for line in f:
        if line.startswith('#'):
            continue
        info = {"channel": None, "playlist": None, "filter": None}
        try:
            query_def = parse.parse_qs(parse.urlparse(line).query)['list'][0]
            info["playlist"] = query_def
            print(query_def)
        except:
            if "channel/" in line:
                o = urlparse(line)
                channel_id = o.path.strip("/channel/")
                info["channel"] = channel_id
                print(channel_id)
        try:
            filter = parse.parse_qs(parse.urlparse(line).query)['filter'][0]
            info["filter"] = filter
            print(filter)
        except:
            print("No filter")

        list.append(info)
    return list


job_list = loadLinkToGenerate()
random.shuffle(job_list)
print(job_list)

for item in job_list:
    i = 0
    try:
        i = random.randint(0, len(apiKeyList) - 1)
        getVideosIds(apiKeyList[i], channel_id=item["channel"], playlist_id=item["playlist"], title_filter=item["filter"])
    except HttpError as err:
        print("An exception occurred: {0}".format(err))
        i = (i + 1) % len(apiKeyList)
        getVideosIds(apiKeyList[i], channel_id=item["channel"], playlist_id=item["playlist"], title_filter=item["filter"])
