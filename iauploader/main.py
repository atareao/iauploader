#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2024 Lorenzo Carbonell <a.k.a. atareao>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE

import os
import sys
import time
import logging
import feedparser
import requests
from internetarchive import get_session
from uuid import uuid4

logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
logger = logging.getLogger(__name__)


def main(feed_url, ia_access, ia_secret, podcast_name, creator_name,
         license_url, language):
    logger.debug("main")
    id = uuid4().__str__()

    logger.debug(f"id: {id}")
    ia_session = get_session(config={
        "s3": {"access": ia_access, "secret": ia_secret}
    })
    logger.debug(f"Parse url: {feed_url}")
    podcast = feedparser.parse(feed_url)

    episodes = sorted(podcast.entries, key=lambda x: x["published_parsed"])
    for index, episode in enumerate(episodes):
        try:
            logger.debug(f"============== {index} ==============")
            logger.debug(episode["id"])
            metadata = {
                "title": episode["title"],
                "mediatype": "audio",
                "collection": "opensource_audio",
                "date": time.strftime("%Y-%m-%d", episode["published_parsed"]),
                "description": episode["summary"],
                "podcast": podcast_name,
                "subject": [tag["term"] for tag in episode["tags"]],
                "creator": creator_name,
                "language": language,
                "licenseurl": license_url
            }
            logger.debug(metadata)
            enclosure = list(filter(lambda x: x.has_key("rel") and
                             x["rel"] == "enclosure",
                                    episode["links"]))[0]["href"]
            logger.debug(enclosure)
            extension = enclosure.split(".")[-1:][0]
            logger.debug(f"Extension: {extension}")
            response = requests.get(enclosure)
            if response.status_code == 200:
                filename = f"{id}.{extension}"
                open(filename, "wb").write(response.content)
                ia_episode = ia_session.get_item(id)
                ia_episode.upload(filename, metadata=metadata, verbose=True)
            else:
                message = (f"HTTP Error: {response.status_code}."
                           " {response.text}")
                raise Exception(message)
        except Exception as exception:
            logger.error(exception)


if __name__ == "__main__":
    feed_url = os.getenv("FEED_URL")
    ia_access = os.getenv("IA_ACCESS")
    ia_secret = os.getenv("IA_SECRET")
    podcast_name = os.getenv("PODCAST_NAME")
    creator_name = os.getenv("CREATOR_NAME")
    license_url = os.getenv("LICENSE_URL", "")
    language = os.getenv("LANGUAGE", "")
    main(feed_url, ia_access, ia_secret, podcast_name, creator_name,
         license_url, language)
