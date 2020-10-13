from .fetch import fetch
from .parse import parse, Entry, FeedData
from .feed import make_rss


def get_rss(key: str) -> str:
    html = fetch(key)
    data = parse(html)
    rss = make_rss(data)
    return rss
