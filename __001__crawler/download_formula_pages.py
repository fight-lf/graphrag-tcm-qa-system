"""Download the first 30 formula detail pages from 中医方剂.xlsx."""

from __future__ import annotations

import os
import sys
import time
import urllib.error

from download_herb_pages import (
    REQUEST_INTERVAL,
    extract_page_text,
    fetch_html,
    safe_filename,
)
from xlsx_reader import read_two_column_xlsx

BASE_DIR = os.path.dirname(__file__)
XLSX_FILE = os.path.join(BASE_DIR, "中医方剂.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "方剂")
ROW_LIMIT = 30


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
    document = f"方剂名字: {name}\n链接地址: {url}\n\n{content}\n"
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(document)


def download_first_rows(limit: int = ROW_LIMIT) -> tuple[int, int, int]:
    rows = read_two_column_xlsx(XLSX_FILE)[:limit]
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
        success_count, skipped_count, failed_count = download_first_rows()
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
