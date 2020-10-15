from argparse import ArgumentParser
from itertools import chain
import logging
from pathlib import Path
import re
import sys
import time
from typing import List
from .. import fetch, parse, FeedData, make_rss

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

# 著者キーがマッチするパターン。
# そもそもURLのパスの一部であり、ファイル名としても用いるので、
# 不都合な入力値は最初にチェックして取り除く。
KEY_PATTERN = re.compile('[-a-zA-Z0-9]+$')

# Yahoo! へのアクセス間隔のデフォルト値(秒)
DEFAULT_HTTP_WAIT = 5


def validate_feeddata(data: FeedData) -> bool:
    '個人ニュースの解析結果を検証する。妥当であれば真を返す。'

    if not data.author:
        LOG.error('解析データが異常です: 著者がありません。')
        return False
    if not data.title:
        LOG.error('解析データが異常です: タイトルがありません。')
        return False
    if not data.url:
        LOG.error('解析データが異常です: URLがありません。')
        return False
    if not data.entries:
        LOG.warning('エントリがありません。')
    return True


class OutputHandler:
    def handle_author_feed(self, key, data: FeedData) -> None:
        pass

    def finish(self) -> None:
        pass


class SingleFileOutputHandler (OutputHandler):
    def __init__(self, outfile):
        self.feed_list = []
        self.outfile = outfile

    def handle_author_feed(self, key, data: FeedData) -> None:
        self.feed_list.append(data)

    def output(self, rss: str) -> None:
        if isinstance(self.outfile, str):
            with open(self.outfile, 'w') as f:
                f.write(rss)
        else:
            self.outfile.write(rss)

    def finish(self) -> None:
        if len(self.feed_list) == 1:
            self.output(make_rss(self.feed_list[0]))
            return

        authors = ', '.join(feed.author for feed in self.feed_list)
        data = FeedData(
            title=f'{authors} - Yahoo!個人ニュース (非公式RSS)',
            url=self.feed_list[0].url,
            author=authors,
            description='',
            entries=sorted(
                chain.from_iterable(feed.entries for feed in self.feed_list),
                key=lambda entry: [entry.pubdate, entry.title], 
                reverse=True)
        )
        self.output(make_rss(data))
        rss = make_rss(data)


class SeparateFileOutputHandler (OutputHandler):
    def __init__(self, dir):
        self.dir = Path(dir)

    def handle_author_feed(self, key: str, data: FeedData) -> None:
        self.dir.mkdir(exist_ok=True)

        file = self.dir / (key.replace('/', '_') + '.rss')
        with open(file, 'w') as f:
            f.write(make_rss(data))


def is_valid_key(key):
    'keyが著者キーとして妥当な文字列なら真を返す。'
    return KEY_PATTERN.match(key)


def read_keys_from_lines(lines):
    COMMENT = re.compile('#.*')
    for line in lines:
        line = COMMENT.sub('', line).strip()
        if line:
            yield line


def read_keys_file(filename) -> List[str]:
    '著者キーのリストをファイルから読み込む。'
    with open(filename) as f:
        return list(read_keys_from_lines(f.readlines()))


def remove_duplicates(lst):
    # dictがキーの順序の保存を保証
    # (Python 3.7以上が必要)
    assert sys.version_info[:3] >= (3, 7, 0), "Python 3.7以上が必要です"
    return list(dict.fromkeys(lst))


class Args:
    # 著者キー
    author_keys = []
    # 出力先ディレクトリ
    output_directory = None
    # 出力先ファイル
    output_file = None
    # アクセス間隔
    http_wait = DEFAULT_HTTP_WAIT


def parse_options():
    parser = ArgumentParser(description='Yahoo!個人ニュースのRSSを出力する。')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-d', '--directory', metavar='DIR',
        help='このディレクトリ以下に著者別にRSSファイルを出力'
    )
    group.add_argument('-o', '--output', metavar='FILE',
        help='出力先ファイル名'
    )
    parser.add_argument('-f', metavar='FILE',
        help='このファイルから著者キーのリストを読み込む'
    )
    parser.add_argument('-w', '--wait', metavar='SECONDS',
        help='Yahoo!個人ニュースへのアクセス間隔(秒)',
        type=int,
        default=DEFAULT_HTTP_WAIT
    )
    parser.add_argument('key', metavar='KEY',
        nargs='+',
        help='RSSを生成する個人ニュースの著者キー'
    )
    args = parser.parse_args()

    if args.f:
        Args.author_keys.extend(read_keys_file(args.f))
    Args.author_keys.extend(args.key)
    Args.author_keys = remove_duplicates(Args.author_keys)
    invalid_keys = [key for key in Args.author_keys if not is_valid_key(key)]
    if invalid_keys:
        Args.author_keys = [key for key in Args.author_keys if is_valid_key(key)]
        LOG.warning("著者キーとして妥当でないものを無視します: %s", ", ".join(invalid_keys))

    if args.directory:
        Args.output_directory = args.directory
        if not Path(args.directory).exists():
            LOG.warning("ディレクトリ %s がありません。作成します。", args.directory)
    else:
        Args.output_file = args.output

    if args.wait < 1:
        LOG.error("指定されたアクセス間隔が不正です。")
        exit(1)
    Args.http_wait = args.wait


def main():
    logging.basicConfig()
    parse_options()
    nerrors = 0
    if Args.output_directory:
        output_handler = SeparateFileOutputHandler(Args.output_directory)
    else:
        output_handler = SingleFileOutputHandler(Args.output_file or sys.stdout)

    wait = 0
    for key in Args.author_keys:
        if nerrors >= 2:
            LOG.error("失敗が複数回発生したため、処理を中断します。")
            exit(1)

        html = data = None
        try:
            time.sleep(wait)
            wait = Args.http_wait
            html = fetch(key)
        except Exception as ex:
            LOG.error('HTML取得に失敗しました。: %s', ex)
            nerrors += 1
            continue

        try:
            data = parse(html)
        except Exception as ex:
            LOG.error('HTML解析に失敗しました。: %s', ex)
            nerrors += 1
            continue

        if not validate_feeddata(data):
            nerrors += 1
            continue

        output_handler.handle_author_feed(key, data)

    output_handler.finish()
    exit(int(nerrors != 0))


if __name__ == '__main__':
    main()
