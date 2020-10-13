# Yahoo個人ニュース購読

指定した著者のYahoo!個人ニュースのRSSを生成します。

## 使い方

Yahoo!個人ニュースの著者のキー(https://news.yahoo.co.jp/byline/foo/ の foo に当たる部分)を指定して
HTMLを取得、RSSを生成します。

```python
from yahoojp_kojin import get_rss
rss = get_rss('foo')
```

HTMLの取得・解析・RSS生成を分けて行う場合:
```python
from yahoojp_kojin import fetch, parse, make_rss
html = fetch('foo')
data = parse(html)
rss = make_rss(data)
```
