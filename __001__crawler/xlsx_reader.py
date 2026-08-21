"""Minimal XLSX reader for two-column sheets written by xlsx_writer."""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET


NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _load_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for si in root.findall("m:si", NS):
        text_parts = [node.text or "" for node in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")]
        strings.append("".join(text_parts))
    return strings


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.get("t")
    value_node = cell.find("m:v", NS)
    if value_node is None or value_node.text is None:
        return ""
    if cell_type == "s":
        return shared_strings[int(value_node.text)]
    return value_node.text


def _column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        return 0
    letters = match.group(1)
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index


def read_two_column_xlsx(path: str) -> list[tuple[str, str]]:
    rows: dict[int, dict[int, str]] = {}

    with zipfile.ZipFile(path) as zf:
        shared_strings = _load_shared_strings(zf)
        sheet = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
        sheet_data = sheet.find("m:sheetData", NS)
        if sheet_data is None:
            return []

        for row in sheet_data.findall("m:row", NS):
            row_number = int(row.get("r", "0"))
            row_values: dict[int, str] = {}
            for cell in row.findall("m:c", NS):
                cell_ref = cell.get("r", "")
                col_number = _column_index(cell_ref)
                row_values[col_number] = _cell_value(cell, shared_strings)
            if row_values:
                rows[row_number] = row_values

    result: list[tuple[str, str]] = []
    for row_number in sorted(rows):
        if row_number == 1:
            continue
        row_values = rows[row_number]
        name = row_values.get(1, "").strip()
        url = row_values.get(2, "").strip()
        if name and url:
            result.append((name, url))
    return result
