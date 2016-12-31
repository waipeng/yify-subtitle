#!/usr/bin/env python3
import re
import sys
from zipfile import ZipFile
import os

import requests
from html2text import HTML2Text

BASE_URL = 'http://www.yifysubtitles.com'


def get(url):
    '''Retrieve page content and use html2text to convert into readable text.'''
    # get webpage content for this url
    r = requests.get(url)
    # raise exception if status code is not 200
    r.raise_for_status()

    # use html2text to transfer html to readable text
    h = HTML2Text(bodywidth=0)
    h.ignore_links = False
    text = h.handle(r.text)

    return text


def search_subtitle(query):
    '''Search subtitle by query in parameter.'''
    text = get('{}/search?q={}'.format(BASE_URL, query))

    # using set here because the html has duplicate links
    results = set()
    # try to find subtitle link in this page
    for line in text.splitlines():
        m = re.search(r' \* .+?\[(.*?)\].*?(\/movie-imdb\/.+)\)', line)
        if m:
            title = m.group(1).encode('ascii', 'ignore')
            link = m.group(2).encode('ascii', 'ignore')
            results.add((title, link))
    if len(results) == 0:
        print("No subs found")
    elif len(results) > 1:
        print("Multiple results found, please refine your search.")
        print("Alternatively, you can search using the id (e.g. tt0094291)")
        for result in results:
            (_, _, uid) = result[1].split('/')
            print("- {} ({})".format(result[0], uid))
    else:
        (title, link) = results.pop()
        print("Found subtitle {} link {}".format(title, link))
        # call get_subtitles() to get all available subtitles
        get_subtitles('{}{}'.format(BASE_URL, link))


def get_subtitles(url):
    '''Find all subtitles url for the movie.'''
    print("Getting subtitle at {}".format(url))
    # get webpage content for this url
    text = get(url)

    # save english subtitles
    subs = []

    for line in text.splitlines():
        if line == '':
            continue
        # find upvote count, subtitle language and subtitle link
        m = re.search(r'(\d+)\| (\w+)\|.*?\((.+?)\)', line)
        if not m:
            continue

        upvote, language, link = m.group(1), m.group(2), m.group(3)
        # we only want english subtitle
        if language == 'English':
            subs.append({
                'up': upvote,
                'link': link
            })
    # sort list by upvote count
    if not subs:
        print('No subs found')
        return
    subs.sort(key=lambda x: int(x['up']), reverse=True)

    # only download subtitle which has the most upvote count
    get_subtitle(subs[0]['link'])


def get_subtitle(url):
    '''Download the specific subtitle.'''
    text = get('{}{}'.format(BASE_URL, url))

    m = re.search(r'\[DOWNLOAD SUBTITLE\]\((.*?)\)', text)
    if m:
        # remove all newline
        link = m.group(1).replace('\n', '')
        print('Download {}'.format(link))

        # use last part of url as file name
        filename = link.split('/')[-1]

        # save the file to current directory
        with open(filename, 'wb') as f:
            f.write(requests.get(link).content)

        # extract subtitles from zip file
        with ZipFile(filename) as zf:
            zf.extractall()

        # after extracting subtitles, remove zip file
        os.remove(filename)


def main():
    try:
        search_subtitle(sys.argv[1])
    except IndexError:
        sys.exit('Usage: yify <movie>')

if __name__ == '__main__':
    main()
