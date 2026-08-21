"""
读取「中药」目录下所有 txt，调用 extract_tcm_knowledge 抽取知识图谱数据，并保存为 JSON。

输出文件可用于后续导入 Neo4j，或转换为 Alpaca 微调格式。
"""

import json
import os
import sys
from pathlib import Path

# 将项目根目录和当前目录加入模块搜索路径，便于导入 common 与 __000__extract_graph_data_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __000__extract_graph_data_utils import _to_json_serializable, extract_tcm_knowledge
from common.path_utils import get_file_path

# 爬虫阶段保存的中药详情 txt 目录
INPUT_DIR = get_file_path("__001__crawler/中药")
# 抽取结果输出路径
OUTPUT_PATH = get_file_path("__002__extract_information/中药详情.json")


def extract_herb_details(
    input_dir: str = INPUT_DIR,
    output_path: str = OUTPUT_PATH,
) -> str:
    """
    遍历输入目录中的 txt 文件，逐篇调用大模型抽取实体与关系，汇总后写入 JSON。

    :param input_dir: 中药 txt 所在目录
    :param output_path: 抽取结果 JSON 文件路径
    :return: 实际写入的文件绝对路径
    """
    input_root = Path(input_dir)
    if not input_root.is_dir():
        raise ValueError(f"输入路径不是有效目录: {input_dir}")

    # rglob 支持递归查找子目录中的 txt 文件
    txt_files = sorted(input_root.rglob("*.txt"))
    if not txt_files:
        raise ValueError(f"输入路径下未找到 txt 文件: {input_dir}")

    results = []
    for txt_file in txt_files:
        text = txt_file.read_text(encoding="utf-8").strip()
        if not text:
            continue

        # 调用 utils 中的抽取链：Prompt -> LLM -> JSON 解析
        graph = _to_json_serializable(extract_tcm_knowledge(text))
        results.append(
            {
                # 保留相对路径，便于回溯原始 txt 来源
                "source_file": str(txt_file.relative_to(input_root)),
                "entities": graph.get("entities", []),
                "relations": graph.get("relations", []),
            }
        )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        # ensure_ascii=False 保证中文正常显示
        json.dump(results, f, ensure_ascii=False, indent=2)

    return str(output_file)


def main() -> None:
    print(f"正在读取: {INPUT_DIR}")
    output = extract_herb_details()
    print(f"已保存到: {output}")


if __name__ == "__main__":
    main()
