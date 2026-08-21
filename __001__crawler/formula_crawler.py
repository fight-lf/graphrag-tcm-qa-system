"""Crawl formula names and links from 中医百科「中医方剂」 page."""

from __future__ import annotations

import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin

from xlsx_writer import write_xlsx

BASE_URL = "https://zhongyibaike.com"
TARGET_URL = f"{BASE_URL}/wiki/%E4%B8%AD%E5%8C%BB%E6%96%B9%E5%89%82"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "中医方剂.xlsx")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GraphRAG-Crawler/1.0"
REQUEST_TIMEOUT = 30


class ContentLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._in_a = False
        self._href = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._in_a = True
            self._href = dict(attrs).get("href", "") or ""
            self._text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_a:
            text = "".join(self._text).strip()
            href = self._href.strip()
            if text and href.startswith("/wiki/"):
                self.links.append((text, urljoin(BASE_URL, href)))
            self._in_a = False

    def handle_data(self, data: str) -> None:
        if self._in_a:
            self._text.append(data)


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT, context=context) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_content_section(html: str) -> str:
    match = re.search(r'<section id="content">(.*?)</section>', html, re.DOTALL)
    if not match:
        raise ValueError("未找到页面正文区域 <section id=\"content\">")
    return match.group(1)


def parse_formula_links(html: str) -> list[tuple[str, str]]:
    content_html = extract_content_section(html)
    parser = ContentLinkParser()
    parser.feed(content_html)

    seen_urls: set[str] = set()
    unique_links: list[tuple[str, str]] = []
    for name, url in parser.links:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        unique_links.append((name, url))
    return unique_links


def crawl() -> list[tuple[str, str]]:
    html = fetch_html(TARGET_URL)
    return parse_formula_links(html)


def save_to_excel(rows: list[tuple[str, str]], output_path: str = OUTPUT_FILE) -> None:
    write_xlsx(
        rows=rows,
        output_path=output_path,
        headers=("方剂名字", "链接地址"),
        sheet_name="中医方剂",
    )


def main() -> int:
    try:
        rows = crawl()
        if not rows:
            print("未抓取到任何方剂链接。", file=sys.stderr)
            return 1

        save_to_excel(rows)
        print(f"抓取完成，共 {len(rows)} 条记录。")
        print(f"已保存到: {OUTPUT_FILE}")
        return 0
    except urllib.error.URLError as exc:
        print(f"网络请求失败: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"页面解析失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
