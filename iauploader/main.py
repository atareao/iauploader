import os
import time
import feedparser
import requests
from internetarchive import get_session
from uuid import uuid4
from pprint import pprint


def main(feed_url, ia_access, ia_secret, podcast_name, creator_name,
         license_url, language):
    id = uuid4().__str__()
    ia_session = get_session(config={
        "s3": {"access": ia_access, "secret": ia_secret}
    })
    url = "http://feeds.feedburner.com/educandogeek"
    podcast = feedparser.parse(url)

    print(podcast.feed.author)
    print(podcast.feed.title)

    exit(0)
    episodes = sorted(podcast.entries, key=lambda x: x["published_parsed"])
    for index, episode in enumerate(episodes):
        pprint(f"============== {index} ==============")
        pprint(episode["id"])
        metadata = {
            "title": episode["title"],
            "mediatype": "audio",
            "collection": "opensource_audio",
            "date": time.strftime("%Y-%m-%d", episode["published_parsed"]),
            "description": episode["summary"],
            "podcast": "Educando Geek",
            "subject": [tag["term"] for tag in episode["tags"]],
            "creator": episode["author"],
            "language": "Spanish",
            "licenseurl": "http://creativecommons.org/publicdomain/zero/1.0/"
        }
        print(metadata)
        enclosure = list(filter(lambda x: x.has_key("rel") and x["rel"] == "enclosure", episode["links"]))[0]["href"]
        pprint(enclosure)
        extension = enclosure.split(".")[-1:][0]
        print(extension)
        response = requests.get(enclosure)
        if response.status_code == 200:
            filename = f"{id}.{extension}"
            open(filename, "wb").write(response.content)
            ia_episode = ia_session.get_item(id)
            ia_episode.upload(filename, metadata=metadata, verbose=True)
            exit(0)


if __name__ == "__main__":
    feed_url = os.getenv("FEED_URL")
    ia_access = os.getenv("IA_ACCESS")
    ia_secret = os.getenv("IA_SECRET")
    podcast_name = os.getenv("PODCAST_NAME")
    creator_name = os.getenv("CREATOR_NAME")
    license_url = os.getenv("LICENSE_URL")
    language = os.getenv("LANGUAGE")
    main(ia_access, ia_secret, podcast_name, creator_name, license_url,
         language)
