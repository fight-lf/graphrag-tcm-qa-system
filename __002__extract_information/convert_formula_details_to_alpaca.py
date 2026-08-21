"""
将「中药详情.json」转换为 Alpaca 格式训练数据。
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.path_utils import get_file_path

INSTRUCTION = "请从以下中医文本中抽取知识图谱结构，包括实体和关系。"

HERB_JSON_PATH = get_file_path("__002__extract_information/方剂数据抽取结果.json")
HERB_TXT_DIR = get_file_path("__001__crawler/方剂2")
OUTPUT_PATH = get_file_path("__002__extract_information/方剂Alpaca数据.json")


def convert_herb_details_to_alpaca(
    json_path: str = HERB_JSON_PATH,
    txt_dir: str = HERB_TXT_DIR,
    output_path: str = OUTPUT_PATH,
) -> tuple[str, int]:
    with open(json_path, encoding="utf-8") as f:
        records = json.load(f)

    txt_root = Path(txt_dir)
    dataset: list[dict[str, str]] = []

    for record in records:
        source_file = record["source_file"]
        txt_path = txt_root / source_file
        if not txt_path.is_file():
            raise FileNotFoundError(f"未找到原始文本文件: {txt_path}")

        text = txt_path.read_text(encoding="utf-8").strip()
        output_obj = {
            "entities": record.get("entities", []),
            "relations": record.get("relations", []),
        }
        dataset.append(
            {
                "instruction": INSTRUCTION,
                "input": text,
                "output": json.dumps(output_obj, ensure_ascii=False),
            }
        )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    return str(output_file), len(dataset)


def main() -> None:
    print(f"正在读取: {HERB_JSON_PATH}")
    output, count = convert_herb_details_to_alpaca()
    print(f"共转换 {count} 条 Alpaca 数据")
    print(f"已保存到: {output}")


if __name__ == "__main__":
    main()
