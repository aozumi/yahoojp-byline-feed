from feedgenerator.django.utils import feedgenerator
from .parse import FeedData

# RSSの仕様に関する参考URL:
# RSS Advisory Board https://www.rssboard.org/

def make_rss(feeddata: FeedData) -> str:
    'RSSを生成する。'

    author = feeddata.author
    if not author:
        raise ValueError('author is required')

    feed = feedgenerator.Rss201rev2Feed(
        title=f'{author} - Yahoo!ニュース個人 (非公式RSS)',
        link=feeddata.url,
        description=feeddata.description,
        language='ja', # see RSS Language Codes https://www.rssboard.org/rss-language-codes
        author_name=author)
    
    for entry in feeddata.entries:
        feed.add_item(
            title=entry.title,
            link=entry.url,
            description=entry.summary,
            author_name=author,
            pubdate=entry.pubdate)

    return feed.writeString('utf-8')
