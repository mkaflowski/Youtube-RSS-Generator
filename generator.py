#!/usr/bin/env python
# -*- coding: utf-8 -*-


import glob
import fnmatch
import time
import urllib
import urllib.parse
import mimetypes
import argparse
from xml.sax import saxutils
import locale
import os
import sys
from datetime import datetime

from optparse import OptionParser

__version__ = 0.2
__date__ = '2014-11-01'
__updated__ = '2020-11-07'

DEBUG = 0
TESTRUN = 0
PROFILE = 0


def getFiles(dirname, extensions=None, recursive=False):
    '''
    Return the list of files (relative paths, starting from dirname) in a given directory.
    Unless a list of the desired file extensions is given, all files in dirname are returned.
    If recursive = True, also look for files in sub directories of dirname.
    Parameters
    ----------
    dirname : string
              path to a directory under the file system.
    extensions : list of string
                 Extensions of the accepted files.
                 Default = None (i.e. return all files).
    recursive : bool
                If True, recursively look for files in sub directories.
                Default = False.
    Returns
    -------
    selectedFiles : list
                A list of file paths.
    Examples
    --------
    >>> import os
    >>> media_dir = os.path.join("test", "media")
    >>> files =  ['1.mp3', '1.mp4', '1.ogg', '2.MP3', 'flac_with_tags.flac', 'mp3_with_tags.mp3']
    >>> expected = [os.path.join(media_dir, f) for f in files]
    >>> getFiles(media_dir) == expected
    True
    >>> expected = [os.path.join(media_dir, f) for f in files]
    >>> sd_1 = os.path.join(media_dir, "subdir_1")
    >>> expected += [os.path.join(sd_1, f) for f in ['2.MP4', '3.mp3', '4.mp3']]
    >>> sd_2 = os.path.join(media_dir, "subdir_2")
    >>> expected += [os.path.join(sd_2, f) for f in ['4.mp4', '5.mp3', '6.mp3']]
    >>> getFiles(media_dir, recursive=True) == expected
    True
    >>> files = ['1.mp3', '2.MP3', 'mp3_with_tags.mp3']
    >>> expected = [os.path.join(media_dir, f) for f in files]
    >>> getFiles(media_dir, extensions=["mp3"]) == expected
    True
    >>> files = ['1.mp3', '1.ogg', '2.MP3', 'mp3_with_tags.mp3']
    >>> expected = [os.path.join(media_dir, f) for f in files]
    >>> expected += [os.path.join(sd_1, f) for f in ['3.mp3', '4.mp3']]
    >>> expected += [os.path.join(sd_2, f) for f in ['5.mp3', '6.mp3']]
    >>> getFiles(media_dir, extensions=["mp3", "ogg"], recursive=True) == expected
    True
    >>> expected = [os.path.join(media_dir, '1.mp4'), os.path.join(sd_1, '2.MP4'), os.path.join(sd_2, '4.mp4')]
    >>> getFiles(media_dir, extensions=["mp4"], recursive=True) == expected
    True
    '''

    if dirname[-1] != os.sep:
        dirname += os.sep

    selectedFiles = []
    allFiles = []
    if recursive:
        for root, dirs, filenames in os.walk(dirname):
            for name in filenames:
                allFiles.append(os.path.join(root, name))
    else:
        allFiles = [f for f in glob.glob(dirname + "*") if os.path.isfile(f)]

    if extensions is not None:
        for ext in set([e.lower() for e in extensions]):
            selectedFiles += [n for n in allFiles if fnmatch.fnmatch(n.lower(), "*{0}".format(ext))]
    else:
        selectedFiles = allFiles

    return sorted(set(selectedFiles))


def buildItem(link, title, guid=None, description="", pubDate=None, indent="   ", extraTags=None):
    '''
    Generate a RSS 2 item and return it as a string.
    Parameters
    ----------
    link : string
           URL of the item.
    title : string
            Title of the item.
    guid : string
           Unique identifier of the item. If no guid is given, link is used as the identifier.
           Default = None.
   description : string
                 Description of the item.
                 Default = ""
    pubDate : string
              Date of publication of the item. Should follow the RFC-822 format,
              otherwise the feed will not pass a validator.
              This method doses (yet) not check the compatibility of pubDate.
              Here are a few examples of correct RFC-822 dates:
              - "Wed, 02 Oct 2002 08:00:00 EST"
              - "Mon, 22 Dec 2014 18:30:00 +0000"
              You can use the following code to gererate a RFC-822 valid time:
              time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(time.time()))
              Default = None (no pubDate tag will be added to the generated item)
    indent : string
             A string of white spaces used to indent the elements of the item.
             3 * len(indent) white spaces will be left before <guid>, <link>, <title> and <description>
             and 2 * len(indent) before item.
    extraTags : a list of dictionaries
                Each dictionary contains the following keys
                - "na1me": name of the tag (mandatory)
                - "value": value of the tag (optional)
                - "params": string or list of string, parameters of the tag (optional)
                Example:
                -------
                Either of the following two dictionaries:
                   {"name" : enclosure, "value" : None, "params" : 'url="file.mp3" type="audio/mpeg" length="1234"'}
                   {"name" : enclosure, "value" : None, "params" : ['url="file.mp3"', 'type="audio/mpeg"', 'length="1234"']}
                will give this tag:
                   <enclosure url="file.mp3" type="audio/mpeg" length="1234"/>
                whereas this dictionary:
                   {"name" : "aTag", "value" : "aValue", "params" : None}
                would give this tag:
                   <aTag>aValue</aTag>
    Returns
    -------
    A string representing a RSS 2 item.
    Examples
    --------
    >>> item = buildItem("my/web/site/media/item1", title = "Title of item 1", guid = "item1",
    ...                  description="This is item 1", pubDate="Mon, 22 Dec 2014 18:30:00 +0000",
    ...                  indent = "   ")
    >>> print(item)
          <item>
             <guid>item1</guid>
             <link>my/web/site/media/item1</link>
             <title>Title of item 1</title>
             <description>This is item 1</description>
             <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
          </item>
    >>> item = buildItem("my/web/site/media/item2", title = "Title of item 2", indent = " ",
    ...                  extraTags=[{"name" : "itunes:duration" , "value" : "06:08"}])
    >>> print(item)
      <item>
       <guid>my/web/site/media/item2</guid>
       <link>my/web/site/media/item2</link>
       <title>Title of item 2</title>
       <description></description>
       <itunes:duration>06:08</itunes:duration>
      </item>
    >>> item = buildItem("my/web/site/media/item2", title = "Title of item 2", indent = " ",
    ...                  extraTags=[{"name" : "enclosure" ,
    ...                              "params" : 'url="http://example.com/media/file.mp3"'
    ...                                         ' type="audio/mpeg" length="1234"'}])
    >>> print(item)
      <item>
       <guid>my/web/site/media/item2</guid>
       <link>my/web/site/media/item2</link>
       <title>Title of item 2</title>
       <description></description>
       <enclosure url="http://example.com/media/file.mp3" type="audio/mpeg" length="1234"/>
      </item>
    >>> item = buildItem("my/web/site/media/item2", title = "Title of item 2", indent = " ",
    ...                  extraTags= [{"name" : "enclosure", "value" : None,
    ...                               "params" :  ['url="file.mp3"', 'type="audio/mpeg"',
    ...                                            'length="1234"']}])
    >>> print(item)
      <item>
       <guid>my/web/site/media/item2</guid>
       <link>my/web/site/media/item2</link>
       <title>Title of item 2</title>
       <description></description>
       <enclosure url="file.mp3" type="audio/mpeg" length="1234"/>
      </item>
    '''

    if guid is None:
        guid = link

    guid = "{0}<guid isPermaLink=\"false\">{1}</guid>\n".format(indent * 3, guid)
    encl = "{0}<enclosure url=\"{1}\"/>\n".format(indent * 3, link)
    link = "{0}<link>{1}</link>\n".format(indent * 3, link)
    title = "{0}<title>{1}</title>\n".format(indent * 3, saxutils.escape(title))
    descrption = "{0}<description>{1}</description>\n".format(indent * 3, saxutils.escape(description))

    if pubDate is not None:
        pubDate = "{0}<pubDate>{1}</pubDate>\n".format(indent * 3, pubDate)
    else:
        pubDate = ""

    extra = ""
    if extraTags is not None:
        for tag in extraTags:
            if tag is None:
                continue

            name = tag["name"]
            value = tag.get("value", None)
            params = tag.get("params", '')
            if params is None:
                params = ''
            if isinstance(params, (list)):
                params = " ".join(params)
            if len(params) > 0:
                params = " " + params

            extra += "{0}<{1}{2}".format(indent * 3, name, params)
            extra += "{0}\n".format("/>" if value is None else ">{0}</{1}>".format(value, name))

    return "{0}<item>\n{1}{2}{3}{4}{5}{6}{7}{0}</item>".format(indent * 2, guid, link, encl, title,
                                                               descrption, pubDate, extra)


def getTitle(filename, use_metadata=False):
    '''
    Get item title from file. If use_metadata is True, try reading title from
    metadata otherwise return file name as the title (without extension).
    Parameters
    ----------
    filename : string
        Path to a file.
    use_metadata : bool
        Whether to use metadata. Default: False.
    Returns
    -------
    title : string
        Item title.
    Examples
    --------
    >>> media_dir = os.path.join("test", "media")
    >>> flac_file = os.path.join(media_dir, 'flac_with_tags.flac')
    >>> mp3_file = os.path.join(media_dir, 'mp3_with_tags.mp3')
    >>> getTitle(flac_file)
    'flac_with_tags'
    >>> getTitle(flac_file, True)
    'Test FLAC file with tags'
    >>> getTitle(mp3_file, True)
    'Test media file with ID3 tags'
    '''
    if use_metadata:
        try:
            # file with ID3 tags
            import eyed3
            meta = eyed3.load(filename)
            if meta and meta.tag is not None:
                return meta.tag.title
        except ImportError:
            pass

        try:
            import mutagen
            from mutagen import id3, mp4, easyid3, easymp4
            from mutagen.mp3 import HeaderNotFoundError
            try:
                # file with ID3 tags
                title = easyid3.EasyID3(filename)["title"]
                if title:
                    return title[0]
            except (id3.ID3NoHeaderError, KeyError):
                try:
                    # file with MP4 tags
                    title = easymp4.EasyMP4(filename)["title"]
                    if title:
                        return title[0]
                except (mp4.MP4StreamInfoError, KeyError):
                    try:
                        # other media types
                        meta = mutagen.File(filename)
                        if meta is not None:
                            title = meta["title"]
                            if title:
                                return title[0]
                    except (KeyError, HeaderNotFoundError):
                        pass
        except ImportError:
            pass

    # fallback to filename as a title, remove extension though
    filename = os.path.basename(filename)
    title, _ = os.path.splitext(filename)
    return title


def fileToItem(host, fname, pubDate, use_metadata=False):
    '''
    Inspect a file name to determine what kind of RSS item to build, and
    return the built item.
    Parameters
    ----------
    host : string
           The hostname and directory to use for the link.
    fname : string
            File name to inspect.
    pubDate : string
              Publication date in RFC 822 format.
    Returns
    -------
    A string representing an RSS item, as with buildItem.
    Examples
    --------
    >>> print(fileToItem('example.com/', 'test/media/1.mp3', 'Mon, 16 Jan 2017 23:55:07 +0000'))
          <item>
             <guid>example.com/test/media/1.mp3</guid>
             <link>example.com/test/media/1.mp3</link>
             <title>1</title>
             <description>1</description>
             <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
             <enclosure url="example.com/test/media/1.mp3" type="audio/mpeg" length="0"/>
          </item>
    >>> print(fileToItem('example.com/', 'test/invalid/checksum.md5', 'Mon, 16 Jan 2017 23:55:07 +0000'))
          <item>
             <guid>example.com/test/invalid/checksum.md5</guid>
             <link>example.com/test/invalid/checksum.md5</link>
             <title>checksum</title>
             <description>checksum</description>
             <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
          </item>
    >>> print(fileToItem('example.com/', 'test/invalid/windows.exe', 'Mon, 16 Jan 2017 23:55:07 +0000'))
          <item>
             <guid>example.com/test/invalid/windows.exe</guid>
             <link>example.com/test/invalid/windows.exe</link>
             <title>windows</title>
             <description>windows</description>
             <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
          </item>
    >>> print(fileToItem('example.com/', 'test/media/mp3_with_tags.mp3', 'Mon, 16 Jan 2017 23:55:07 +0000'))
          <item>
             <guid>example.com/test/media/mp3_with_tags.mp3</guid>
             <link>example.com/test/media/mp3_with_tags.mp3</link>
             <title>mp3_with_tags</title>
             <description>mp3_with_tags</description>
             <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
             <enclosure url="example.com/test/media/mp3_with_tags.mp3" type="audio/mpeg" length="803"/>
          </item>
    >>> print(fileToItem('example.com/', 'test/media/mp3_with_tags.mp3', 'Mon, 16 Jan 2017 23:55:07 +0000', True))
          <item>
             <guid>example.com/test/media/mp3_with_tags.mp3</guid>
             <link>example.com/test/media/mp3_with_tags.mp3</link>
             <title>Test media file with ID3 tags</title>
             <description>Test media file with ID3 tags</description>
             <pubDate>Mon, 16 Jan 2017 23:55:07 +0000</pubDate>
             <enclosure url="example.com/test/media/mp3_with_tags.mp3" type="audio/mpeg" length="803"/>
          </item>
    '''

    fileMimeType = mimetypes.guess_type(fname)[0]

    if fileMimeType is not None and ("audio" in fileMimeType or "video" in fileMimeType or "image" in fileMimeType):
        tagParams = "url=\"{0}\" type=\"{1}\" length=\"{2}\"".format(fileURL, fileMimeType, os.path.getsize(fname))
        enclosure = {"name": "enclosure", "value": None, "params": tagParams}
    else:
        enclosure = None

    title = getTitle(fname, use_metadata)

    return buildItem(link=fileURL, title=title,
                     guid=fileURL, description=title,
                     pubDate=pubDate, extraTags=[enclosure])


def generate(outfile, title, description, author, link, imgurl, videos):
    outfp = open(outfile, "w", encoding='utf-8')

    outfp.write(
        '<?xml version="1.0" encoding="UTF-8"?><rss xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom" version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:anchor="https://anchor.fm/xmlns">\n')
    outfp.write('   <channel>\n')
    outfp.write('      <atom:link href="{0}" rel="self" type="application/rss+xml" />\n'.format(link))
    outfp.write('      <title>{0}</title>\n'.format(saxutils.escape(title.encode('utf-8', 'replace').decode())))
    outfp.write('      <description>{0}</description>\n'.format(description).encode('utf-8', 'replace').decode())
    outfp.write('      <itunes:author>{0}</itunes:author>\n'.format(author.encode('utf-8', 'replace').decode()))
    outfp.write('      <link>{0}</link>\n'.format(link))

    outfp.write("      <image>\n")
    outfp.write("         <url>{0}</url>\n".format(imgurl))
    outfp.write("         <title>{0}</title>\n".format(saxutils.escape(title)))
    outfp.write("         <link>{0}</link>\n".format(link))
    outfp.write("      </image>\n")
    outfp.write('      <itunes:image href="{0}"/>\n'.format(imgurl))

    for video in videos:
        outfp.write(buildItem(link="https://www.youtube.com/watch?v=" + video["videoId"], title=video["title"],
                              guid=video["videoId"], description=video["desc"],
                              pubDate=video["published"]).encode('utf-8', 'replace').decode() + "\n")

    # for item in items:
    #     outfp.write(item.encode('utf-8', 'replace').decode() + "\n")

    outfp.write('')
    outfp.write('   </channel>\n')
    outfp.write('</rss>\n')

    if outfp != sys.stdout:
        outfp.close()
    print("Generating RSS")