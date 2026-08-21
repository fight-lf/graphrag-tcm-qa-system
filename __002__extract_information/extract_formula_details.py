"""
读取「方剂」目录下所有 txt，调用 extract_tcm_knowledge 抽取数据并保存为 JSON。
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __000__extract_graph_data_utils import _to_json_serializable, extract_tcm_knowledge
from common.path_utils import get_file_path

INPUT_DIR = get_file_path("__001__crawler/方剂")
OUTPUT_PATH = get_file_path("__002__extract_information/方剂详情.json")


def extract_formula_details(
    input_dir: str = INPUT_DIR,
    output_path: str = OUTPUT_PATH,
) -> str:
    input_root = Path(input_dir)
    if not input_root.is_dir():
        raise ValueError(f"输入路径不是有效目录: {input_dir}")

    txt_files = sorted(input_root.rglob("*.txt"))
    if not txt_files:
        raise ValueError(f"输入路径下未找到 txt 文件: {input_dir}")

    results = []
    for txt_file in txt_files:
        text = txt_file.read_text(encoding="utf-8").strip()
        if not text:
            continue

        graph = _to_json_serializable(extract_tcm_knowledge(text))
        results.append(
            {
                "source_file": str(txt_file.relative_to(input_root)),
                "entities": graph.get("entities", []),
                "relations": graph.get("relations", []),
            }
        )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return str(output_file)


def main() -> None:
    print(f"正在读取: {INPUT_DIR}")
    output = extract_formula_details()
    print(f"已保存到: {output}")


if __name__ == "__main__":
    main()
