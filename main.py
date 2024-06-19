#!/bin/python
"""
Fetches news from RSS feeds, processes the news data, and generates an HTML file 
containing the news items.
"""

import json
import subprocess
import sys
import shutil
from pathlib import Path
from dataclasses import dataclass
import datetime

SFEED_UPDATE_COMMAND = "sfeed_update"
SFEED_JSON_COMMAND = "sfeed_json"
SFEEDRC_PATH = "sfeedrc"
FEEDS_DIR_PATH = "feeds"
JSON_FILE_PATH = "result.json"
HTML_FILE_PATH = "public/index.html"

HTML_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
  <title>sfeed</title>
  <link rel="stylesheet" href="./style.css">
  <link rel="icon" href="./favicon.ico" type="image/x-icon">
</head>
<body>
"""

HTML_FOOTER = """
</body></html>"""


@dataclass
class NewsItem:
    """
    A class to represent a news item.
    """

    title: str
    link: str
    date_published: datetime.datetime


def parse_published_date(dt: str):
    """
    Parses the published date from the provided string and returns a datetime object
    or None if the date is older than 4 days or if an error occurred while
    parsing the date.
    """

    date_format = "%Y-%m-%dT%H:%M:%SZ"
    try:
        datetime_obj = datetime.datetime.strptime(dt, date_format)

        current_date = datetime.datetime.now()
        four_days_ago = current_date - datetime.timedelta(days=4)

        if datetime_obj < four_days_ago:
            return None

        return datetime_obj

    except ValueError as err:
        print(f"Failed to parse published date: {err}")
        return None


def parse_json_data(data) -> list[NewsItem]:
    """
    Parses news items from the provided JSON data.

    Returns A list of parsed NewsItem objects.
    """

    parsed_news: list[NewsItem] = []

    items = data["items"]
    for item in items:

        datetime_obj = parse_published_date(item["date_published"])
        if datetime_obj is None:
            continue

        news_item = NewsItem(item["title"], item["url"], datetime_obj)
        parsed_news.append(news_item)

    return parsed_news


def write_to_html_file(parsed_news: list[NewsItem]):
    """
    Writes the provided parsed news items to an HTML file.
    """

    parsed_news = sorted(parsed_news, key=lambda i: i.date_published, reverse=True)

    with open(HTML_FILE_PATH, "w", encoding="Utf-8") as html_file:

        # Append the html page header
        html_file.write(HTML_HEADER)
        html_file.write("  <ul>\n")

        for news_item in parsed_news:
            dp = news_item.date_published.date()
            il = news_item.link
            it = news_item.title
            html_file.write(
                f'    <li><span> {dp}</span> <a href="{il}">{it}</a></li>\n'
            )

        html_file.write("  </ul>")

        # Append the html page footer
        html_file.write(HTML_FOOTER)


def generate_html_file():
    """
    Loads the JSON file, parses the news items, and writes them to a generated
    HTML file.
    """

    with open(JSON_FILE_PATH, "r", encoding="Utf-8") as file:
        data = json.load(file)

    parsed_news = parse_json_data(data)
    write_to_html_file(parsed_news)


def fetch_rss_feeds():
    """
    Runs the sfeed_update command to fetch RSS news
    """

    try:
        # Delete the old feeds if exists
        if Path(FEEDS_DIR_PATH).exists():
            shutil.rmtree(FEEDS_DIR_PATH)

        # Fetch the feeds
        subprocess.run(f"{SFEED_UPDATE_COMMAND} {SFEEDRC_PATH}", shell=True, check=True)

    # It should not panic if it fails to fetch one or more feeds
    except subprocess.CalledProcessError as err:
        print(f"An error occurred while fetching the news: {err}")

    except FileNotFoundError as err:
        print(f"An error occurred while removing feeds directory: {err}")
        sys.exit(1)


def generate_json_file():
    """
    Converts the fetched news to JSON using sfeed_json.
    """

    try:
        # Convert the fetched news to json
        subprocess.run(
            f"{SFEED_JSON_COMMAND} {FEEDS_DIR_PATH}/* > {JSON_FILE_PATH} ",
            shell=True,
            check=True,
        )

    except subprocess.CalledProcessError as err:
        print(f"An error occurred while running sfeed_json: {err}")
        sys.exit(1)


def main():
    """
    Fetches news from an RSS feed and generates an HTML file containing these
    news items.

    The function performs the following steps:
    1. Fetches the latest RSS news feeds.
    2. Converts the fetched news into a JSON file.
    3. Parses the JSON file and generates an HTML file with the news items.
    """

    fetch_rss_feeds()
    generate_json_file()
    generate_html_file()


main()
