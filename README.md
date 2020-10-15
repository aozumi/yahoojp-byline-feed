# Yahoo個人ニュース購読

指定した著者のYahoo!個人ニュースのRSSを生成します。

## 使い方 (コード)

Yahoo!個人ニュースの著者のキー(https://news.yahoo.co.jp/byline/foo/ の foo に当たる部分)を指定して
HTMLを取得、RSSを生成します。

```python
from yahoojp_byline import get_rss
rss = get_rss('foo')
```

HTMLの取得・解析・RSS生成を分けて行う場合:
```python
from yahoojp_byline import fetch, parse, make_rss
html = fetch('foo')
data = parse(html)
rss = make_rss(data)
```

## 使い方 (コマンド)

```
% python3 -m yahoojp_byline.command.main -d DIR [-w SECONDS] KEY ...
```
引数 _KEY_ には著者キーを並べます。
ディレクトリ _DIR_ の下に _KEY_`.rss` として著者別にRSSファイルを生成します。

`-w`オプションではHTTPリクエストの間隔(秒)を整数で指定できます。
