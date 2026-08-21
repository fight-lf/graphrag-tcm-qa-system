"""Format crawled txt files: remove links and fix excessive line breaks."""

from __future__ import annotations

import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET_DIRS = [BASE_DIR / "中药", BASE_DIR / "方剂"]

LINK_PATTERN = re.compile(r"^链接地址:\s*https?://\S+\s*$")
NOISE_PATTERN = re.compile(r"^\d*#+$")
NUMBERED_ITEM_PATTERN = re.compile(r"^\d+[、．.]")
LIST_ITEM_PATTERN = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩\d]+[\.、．]")
BRACKET_LABEL_PATTERN = re.compile(r"^【.+】$")


def is_numbered_item(line: str) -> bool:
    return bool(NUMBERED_ITEM_PATTERN.match(line))

FIELD_LABELS = {
    "名称",
    "出处",
    "分类",
    "组成",
    "解释",
    "方解",
    "功效",
    "功用",
    "主治",
    "用法",
    "注意",
    "来源",
    "性味",
    "性状",
    "经脉",
    "用法用量",
    "注意禁忌",
    "运用",
    "附方",
    "别名",
    "异名",
    "禁忌",
    "制备",
    "歌诀",
    "证治机理",
    "配伍特点",
    "化裁",
    "附注",
}

SECTION_SUFFIXES = ("的药方", "的功效", "的效果", "的种植和炮制")


def next_nonempty(lines: list[str], start: int) -> int:
    index = start
    while index < len(lines) and not lines[index]:
        index += 1
    return index


def is_section_header(line: str) -> bool:
    return any(line.endswith(suffix) for suffix in SECTION_SUFFIXES)


def is_field_label(line: str) -> bool:
    return line in FIELD_LABELS or bool(BRACKET_LABEL_PATTERN.match(line))


def is_list_item(line: str) -> bool:
    return bool(LIST_ITEM_PATTERN.match(line))


def is_short_fragment(line: str) -> bool:
    if not line or len(line) > 30:
        return False
    if is_field_label(line) or is_section_header(line) or is_list_item(line) or is_numbered_item(line):
        return False
    return not re.search(r"[。！？；：，、（《》]", line)


def ends_sentence(text: str) -> bool:
    return bool(re.search(r"[。！？；：》）】\.]$", text))


def is_alias_summary(line: str) -> bool:
    return ("，" in line or "、" in line) and len(line) >= 8


def merge_alias_block(lines: list[str], start: int) -> tuple[str, int]:
    values = [lines[start]]
    index = start + 1
    while index < len(lines):
        current = lines[index]
        if not current or not is_short_fragment(current):
            break
        values.append(current)
        index += 1
    return "、".join(values), index


def skip_duplicate_alias_lines(lines: list[str], start: int) -> int:
    index = start
    while index < len(lines):
        current = lines[index]
        if not current:
            index += 1
            continue
        if is_section_header(current) or is_field_label(current) or is_list_item(current):
            break
        if is_short_fragment(current):
            index += 1
            continue
        break
    return index


def preprocess_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if LINK_PATTERN.match(line):
            continue
        if NOISE_PATTERN.match(line):
            continue
        lines.append(line)
    return lines


def format_lines(lines: list[str]) -> list[str]:
    result: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line:
            index += 1
            continue

        if line.startswith(("药材名字:", "方剂名字:")):
            result.append(line)
            index += 1
            continue

        if is_section_header(line):
            if result and result[-1] != "":
                result.append("")
            result.append(line)
            index += 1
            continue

        if is_field_label(line):
            value_index = next_nonempty(lines, index + 1)
            if value_index >= len(lines):
                result.append(line)
                index += 1
                continue

            next_line = lines[value_index]
            if is_field_label(next_line) or is_section_header(next_line):
                result.append(line)
                index += 1
                continue

            if is_numbered_item(next_line):
                result.append(f"{line}：")
                result.append(next_line)
                value_index += 1
                while value_index < len(lines):
                    candidate = lines[value_index]
                    if not candidate:
                        value_index += 1
                        continue
                    if not is_numbered_item(candidate):
                        break
                    result.append(candidate)
                    value_index += 1
                index = value_index
                continue

            if BRACKET_LABEL_PATTERN.match(line) and (
                is_numbered_item(next_line) or is_list_item(next_line)
            ):
                result.append(line)
                index = value_index
                continue

            if is_short_fragment(next_line):
                merged_values, next_index = merge_alias_block(lines, value_index)
                result.append(f"{line}：{merged_values}")
                index = next_index
                continue

            result.append(f"{line}：{next_line}")
            index = value_index + 1
            continue

        if is_list_item(line) or is_numbered_item(line):
            result.append(line)
            index += 1
            continue

        if line.startswith("【") and not BRACKET_LABEL_PATTERN.match(line):
            result.append(line)
            index += 1
            continue

        if is_alias_summary(line):
            result.append(line)
            index = skip_duplicate_alias_lines(lines, index + 1)
            continue

        paragraph = line
        next_index = index + 1
        while next_index < len(lines):
            candidate = lines[next_index]
            if not candidate:
                next_index += 1
                continue
            if (
                is_field_label(candidate)
                or is_section_header(candidate)
                or is_list_item(candidate)
                or is_numbered_item(candidate)
                or candidate.startswith("【")
            ):
                break
            if is_short_fragment(candidate) or is_alias_summary(candidate):
                break
            if ends_sentence(paragraph):
                break
            paragraph += candidate
            next_index += 1

        result.append(paragraph)
        index = next_index

    cleaned: list[str] = []
    for line in result:
        if line == "" and (not cleaned or cleaned[-1] == ""):
            continue
        cleaned.append(line)
    return cleaned


def format_text(text: str) -> str:
    lines = preprocess_lines(text)
    formatted = format_lines(lines)
    return "\n".join(formatted).strip() + "\n"


def format_directory(directory: Path) -> int:
    if not directory.exists():
        return 0

    count = 0
    for txt_file in sorted(directory.glob("*.txt")):
        original = txt_file.read_text(encoding="utf-8")
        updated = format_text(original)
        txt_file.write_text(updated, encoding="utf-8")
        count += 1
    return count


def main() -> None:
    total = 0
    for directory in TARGET_DIRS:
        count = format_directory(directory)
        print(f"已整理 {count} 个文件: {directory}")
        total += count
    print(f"全部完成，共整理 {total} 个 txt 文件。")


if __name__ == "__main__":
    main()
