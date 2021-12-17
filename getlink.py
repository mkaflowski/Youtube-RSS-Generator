#!/usr/bin/env python
import argparse
import sys


from pytube import YouTube

program_usage = "downloader [OPTIONS]"
program_longdesc = "Video link generator"
argv = sys.argv[1:]
parser = argparse.ArgumentParser(usage=program_usage, description=program_longdesc,
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-v", "--vid", dest="vid",
                    help="Video ID.\n"
                    , metavar="VID")

opts = parser.parse_args(argv)
video_id = opts.vid

yt = YouTube('http://youtube.com/{0}'.format(video_id))

stream = yt.streams.filter(res="720p", file_extension='mp4', only_video=False).first()
if stream is None:
    stream = yt.streams.filter(res="360p", file_extension='mp4', only_video=False).first()
if stream is None:
    stream = yt.streams.filter(only_audio=True).last()
if stream is not None:
    url2 = stream.url
print(url2)