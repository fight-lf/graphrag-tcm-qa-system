"""Download herb detail pages listed in 中药大全.xlsx and save as txt files."""

from __future__ import annotations

import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import quote, urlsplit, urlunsplit

from xlsx_reader import read_two_column_xlsx

BASE_DIR = os.path.dirname(__file__)
XLSX_FILE = os.path.join(BASE_DIR, "中药大全.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "中药")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GraphRAG-Crawler/1.0"
REQUEST_TIMEOUT = 30
REQUEST_INTERVAL = 0.5
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class TextExtractor(HTMLParser):
    BLOCK_TAGS = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "br"}
    SKIP_TAGS = {"script", "style", "noscript"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def encode_url(url: str) -> str:
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme, parts.netloc, quote(parts.path, safe="/%"), parts.query, parts.fragment))


def fetch_html(url: str) -> str:
    request = urllib.request.Request(encode_url(url), headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT, context=context) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_page_text(html: str) -> str:
    match = re.search(r'<section id="content">(.*?)</section>', html, re.DOTALL)
    if not match:
        raise ValueError("未找到页面正文区域")
    parser = TextExtractor()
    parser.feed(match.group(1))
    return parser.get_text()


def safe_filename(name: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("_", name.strip())
    cleaned = cleaned.rstrip(". ")
    return cleaned or "unknown"


def assign_output_paths(rows: list[tuple[str, str]]) -> list[tuple[str, str, str]]:
    name_count: dict[str, int] = {}
    assigned: list[tuple[str, str, str]] = []
    for name, url in rows:
        base_name = safe_filename(name)
        count = name_count.get(base_name, 0) + 1
        name_count[base_name] = count
        filename = f"{base_name}.txt" if count == 1 else f"{base_name}_{count}.txt"
        assigned.append((name, url, os.path.join(OUTPUT_DIR, filename)))
    return assigned


def save_page_text(output_path: str, name: str, url: str, content: str) -> None:
    document = f"药材名字: {name}\n链接地址: {url}\n\n{content}\n"
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(document)


def download_all() -> tuple[int, int, int]:
    rows = read_two_column_xlsx(XLSX_FILE)
    if not rows:
        raise ValueError(f"未从 Excel 读取到数据: {XLSX_FILE}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    success_count = 0
    skipped_count = 0
    failed_count = 0

    total = len(rows)
    for index, (name, url, output_path) in enumerate(assign_output_paths(rows), start=1):
        if os.path.exists(output_path):
            print(f"[{index}/{total}] 跳过已存在: {os.path.basename(output_path)}")
            skipped_count += 1
            continue

        try:
            html = fetch_html(url)
            text = extract_page_text(html)
            save_page_text(output_path, name, url, text)
            success_count += 1
            print(f"[{index}/{total}] 已保存: {os.path.basename(output_path)}")
        except (urllib.error.URLError, ValueError, TimeoutError) as exc:
            failed_count += 1
            print(f"[{index}/{total}] 失败 ({name}): {exc}", file=sys.stderr)

        if index < total:
            time.sleep(REQUEST_INTERVAL)

    return success_count, skipped_count, failed_count


def main() -> int:
    try:
        success_count, skipped_count, failed_count = download_all()
        print(
            f"下载完成。成功 {success_count} 个，跳过 {skipped_count} 个，失败 {failed_count} 个。"
        )
        print(f"保存目录: {OUTPUT_DIR}")
        return 0 if failed_count == 0 else 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
