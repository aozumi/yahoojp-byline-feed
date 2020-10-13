import requests
from urllib.parse import quote


def top_url(key: str) -> str:
    'Yahoo!個人ニュースの指定した著者のトップページURLを返す。'
    return 'https://news.yahoo.co.jp/byline/' + quote(key, safe='')


def fetch(key: str) -> str:
    '''Yahoo!個人ニュースの指定した著者のトップページを取得する。
    取得したHTMLを文字列で返す。
    '''
    r = requests.get(top_url(key))
    r.raise_for_status()
    return r.text
