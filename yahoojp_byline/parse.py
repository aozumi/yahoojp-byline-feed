from bs4 import BeautifulSoup
import re
from datetime import datetime
from dateutil.tz import gettz
from collections import namedtuple
from typing import Optional, List

TZ_TOKYO = gettz('Asia/Tokyo')

Entry = namedtuple('Entry', ('url', 'title', 'summary', 'pubdate', 'thumbnail'))
FeedData = namedtuple('FeedData', ('title', 'url', 'author', 'description', 'entries'))


def select1(elem, spec: str):
    'elem以下でspecに合致する最初の要素を返す。'

    results = elem.select(spec)
    return results and results[0] or None


def safe_int(x: Optional[str]) -> Optional[int]:
    return int(x) if x else None


def parse_pubdate(date_str: str, this_year :Optional[int] =None) -> Optional[datetime]:
    '''Yahoo!個人ニュースの日時を解析してdatetimeインスタンスを返す。

    Yahoo!個人ニュースでは今年の日付から年を省略して表示する。このため
    解析実行時点の年を自動的に補うが、この年を変更したい場合は引数
    this_yearに指定する。

    戻り値のdatetimeはtzinfoに日本標準時を設定したaware datetime。

    >>> dt = parse_pubdate('9/2(水) 8:32', 2020)
    >>> dt.replace(tzinfo=None)
    datetime.datetime(2020, 9, 2, 8, 32)
    >>> dt.tzinfo.utcoffset(dt)
    datetime.timedelta(seconds=32400)
    >>> parse_pubdate('2019/12/3(火) 22:26').replace(tzinfo=None)
    datetime.datetime(2019, 12, 3, 22, 26)
    '''
    date_regexp = r'(?:([0-9]{4})/)?([1-9]|1[012])/([123]?[0-9])'
    time_regexp = r'([0-9]{1,2}):([0-9]{1,2})'
    m = re.search(date_regexp + '.*?' + time_regexp, date_str)
    if m:
        year = safe_int(m.group(1))
        month, day, hour, minute = map(int, m.groups()[1:])
        if not year:
            if this_year is None:
                this_year = datetime.now(TZ_TOKYO).year
            year = this_year
        return datetime(year, month, day, hour, minute, tzinfo=TZ_TOKYO)
    else:
        return None


def extract_entry_link(entry_elem) -> Optional[str]:
    link = select1(entry_elem, 'a.entryBody')
    return link and link['href']


def extract_entry_thumbnail(entry_elem) -> Optional[str]:
    thumb = select1(entry_elem, 'dd.thumb img')
    return thumb and thumb['src']


def extract_entry_title(entry_elem) -> Optional[str]:
    ttl = select1(entry_elem, 'dt.ttl')
    return ttl and ''.join(ttl.strings)


def extract_entry_summary(entry_elem) -> Optional[str]:
    elem = select1(entry_elem, 'dd.summary')
    return elem and ''.join(elem.strings)


def extract_entry_pubdate(entry_elem) -> Optional[datetime]:
    elem = select1(entry_elem, 'dd.pubdate')
    return elem and parse_pubdate(''.join(elem.strings))


def parse_entry(entry_elem) -> Entry:
    url = extract_entry_link(entry_elem)
    thumbnail = extract_entry_thumbnail(entry_elem)
    title = extract_entry_title(entry_elem)
    summary = extract_entry_summary(entry_elem)
    pubdate = extract_entry_pubdate(entry_elem)
    return Entry(url, title, summary, pubdate, thumbnail)


def extract_entries(soup) -> List[Entry]:
    list = soup.find(id='athr_al')
    if list is None:
        return []
    entry_elems = list.find_all('li', **{'class': 'entry'})
    entries = [ parse_entry(x) for x in entry_elems ]
    return entries


def extract_title(soup) -> Optional[str]:
    title_elem = select1(soup, 'title')
    return title_elem and title_elem.string


def extract_description(soup) -> Optional[str]:
    desc_elem = select1(soup, 'meta[name="description"]')
    return desc_elem and desc_elem['content']


def extract_canonical_url(soup) -> Optional[str]:
    canon_elem = select1(soup, 'link[rel="canonical"]')
    return canon_elem and canon_elem['href']


def extract_author(soup) -> Optional[str]:
    title_elem = select1(soup, 'head title')
    if not title_elem:
        return None
    m = re.match('(.+)の記事一覧', title_elem.string)
    return m and m.group(1) or None


def parse(html: str) -> FeedData:
    soup = BeautifulSoup(html, 'html5lib')

    title = extract_title(soup)
    author = extract_author(soup)
    description = extract_description(soup)
    canonical_url = extract_canonical_url(soup)
    entries = extract_entries(soup)
    return FeedData(title, canonical_url, author, description, entries)
