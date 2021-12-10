import googleapiclient.discovery
from googleapiclient.errors import HttpError
from pytube import YouTube
from datetime import datetime as dt
import generator
from apiKey import apiKeyList
import os
import sys

catalog_path = os.path.dirname(sys.argv[0])


def getVideosIds(key, channe_id, title_filter = None):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=key)

    request = youtube.channels().list(
        part="snippet",
        id=channe_id,
    )
    response = request.execute()
    print(response)
    title = response["items"][0]["snippet"]["title"]
    desc = response["items"][0]["snippet"]["description"]
    author = title
    id = response["items"][0]["id"]
    link = "https://www.youtube.com/channel/" + id
    print(link)
    imgurl = response["items"][0]["snippet"]["thumbnails"]["medium"]["url"]

    request = youtube.search().list(
        part="snippet,id",
        channelId=channe_id,
        maxResults=50,
        type="video",
        order="date"
    )
    response = request.execute()
    print(response)

    items = []
    items += response["items"]
    if title_filter is not None:
        items = list(filter(lambda it: title_filter in it["snippet"]["title"].lower(), items))
    limit = 5
    items = items[:limit]
    print(f"total: {len(items)}")

    videos = []
    for item in items:
        print(item)
        # try:
        video_id = item["id"]["videoId"]
        title2 = item["snippet"]["title"]
        desc2 = item["snippet"]["description"]
        image2 = item["snippet"]["thumbnails"]["medium"]["url"]

        published_at = item["snippet"]["publishedAt"].replace("T", " ").replace("Z", " ").rstrip()
        date_obj = dt.strptime(published_at, '%Y-%m-%d %H:%M:%S')
        published_at = dt.strftime(date_obj, "%a, %d %b %Y %H:%M:%S +0000")

        yt = YouTube('http://youtube.com/{0}'.format(video_id))
        url2 = yt.streams.filter(res="480p", file_extension='mp4').first().url

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
        print("The new directory is created! "+generated_catalog_path)

    generator.generate(generated_catalog_path + channe_id + ".rss", title, desc, author, link, imgurl, videos)


def disableSSL():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context


# disableSSL()

try:
    getVideosIds(apiKeyList[0], "UCapiydRNc88rlAYcgzjPYGg", "rozmowa")
except HttpError as err:
    print("An exception occurred: {0}".format(err))
    getVideosIds(apiKeyList[1], "UCapiydRNc88rlAYcgzjPYGg", "rozmowa")
