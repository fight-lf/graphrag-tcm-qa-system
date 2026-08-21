"""Import TCM knowledge graph data from Alpaca JSON files into Neo4j."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.config import Config

BASE_DIR = Path(__file__).parent
HERB_ALPACA_FILE = PROJECT_ROOT / "__002__extract_information" / "中药Alpaca数据.json"
FORMULA_ALPACA_FILE = PROJECT_ROOT / "__002__extract_information" / "方剂Alpaca数据.json"

ENTITY_TYPES = {"Symptom", "Disease", "Formula", "Herb", "Effect", "Source"}
RELATION_TYPES = {
    "TREATS_DISEASE",
    "ALLEVIATES_SYMPTOM",
    "HAS_EFFECT",
    "HAS_INGREDIENT",
    "HAS_SYMPTOM",
    "FROM_SOURCE",
}
BATCH_SIZE = 200


def load_alpaca_records(*paths: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"未找到数据文件: {path}")
        with path.open("r", encoding="utf-8") as file:
            records.extend(json.load(file))
    return records


def parse_graph_data(records: list[dict[str, Any]]) -> tuple[dict[tuple[str, str], dict], set[tuple]]:
    entities: dict[tuple[str, str], dict[str, Any]] = {}
    relations: set[tuple] = set()

    for record in records:
        output_text = record.get("output", "")
        if not output_text:
            continue

        graph = json.loads(output_text)
        for entity in graph.get("entities", []):
            name = str(entity.get("name", "")).strip()
            entity_type = str(entity.get("type", "")).strip()
            if not name or entity_type not in ENTITY_TYPES:
                continue

            key = (entity_type, name)
            attributes = clean_attributes(entity.get("attributes"))
            if key not in entities:
                entities[key] = {"type": entity_type, "name": name, "attributes": attributes}
            else:
                entities[key]["attributes"].update(attributes)

        for relation in graph.get("relations", []):
            subject = str(relation.get("subject", "")).strip()
            object_name = str(relation.get("object", "")).strip()
            subject_type = str(relation.get("subject_type", "")).strip()
            object_type = str(relation.get("object_type", "")).strip()
            rel_type = str(relation.get("relation", "")).strip()

            if not all([subject, object_name, subject_type, object_type, rel_type]):
                continue
            if subject_type not in ENTITY_TYPES or object_type not in ENTITY_TYPES:
                continue
            if rel_type not in RELATION_TYPES:
                continue

            relations.add((subject, subject_type, rel_type, object_name, object_type))

            for entity_type, entity_name in ((subject_type, subject), (object_type, object_name)):
                key = (entity_type, entity_name)
                if key not in entities:
                    entities[key] = {"type": entity_type, "name": entity_name, "attributes": {}}

    return entities, relations


def clean_attributes(attributes: Any) -> dict[str, Any]:
    if not isinstance(attributes, dict):
        return {}
    return {key: value for key, value in attributes.items() if value is not None}


def create_indexes(session) -> None:
    for entity_type in ENTITY_TYPES:
        session.run(
            f"CREATE INDEX IF NOT EXISTS FOR (n:{entity_type}) ON (n.name)"
        )


def clear_database(session) -> None:
    session.run("MATCH (n) DETACH DELETE n")


def import_entities(session, entities: dict[tuple[str, str], dict[str, Any]]) -> int:
    grouped: dict[str, list[dict[str, Any]]] = {entity_type: [] for entity_type in ENTITY_TYPES}
    for entity in entities.values():
        grouped[entity["type"]].append(
            {"name": entity["name"], "attributes": entity["attributes"]}
        )

    total = 0
    for entity_type, rows in grouped.items():
        if not rows:
            continue
        query = f"""
        UNWIND $rows AS row
        MERGE (n:{entity_type} {{name: row.name}})
        SET n += row.attributes
        """
        for start in tqdm(range(0, len(rows), BATCH_SIZE), desc=f"导入节点 {entity_type}", leave=False):
            batch = rows[start : start + BATCH_SIZE]
            session.run(query, rows=batch)
            total += len(batch)
    return total


def import_relations(session, relations: set[tuple]) -> int:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for subject, subject_type, rel_type, object_name, object_type in relations:
        key = (subject_type, rel_type, object_type)
        grouped.setdefault(key, []).append({"subject": subject, "object": object_name})

    total = 0
    for (subject_type, rel_type, object_type), rows in grouped.items():
        query = f"""
        UNWIND $rows AS row
        MATCH (s:{subject_type} {{name: row.subject}})
        MATCH (o:{object_type} {{name: row.object}})
        MERGE (s)-[r:{rel_type}]->(o)
        """
        for start in tqdm(
            range(0, len(rows), BATCH_SIZE),
            desc=f"导入关系 {rel_type}",
            leave=False,
        ):
            batch = rows[start : start + BATCH_SIZE]
            session.run(query, rows=batch)
            total += len(batch)
    return total


def count_graph(session) -> dict[str, int]:
    node_count = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
    rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
    return {"nodes": node_count, "relationships": rel_count}


def import_alpaca_data(clear_first: bool = False) -> dict[str, int]:
    records = load_alpaca_records(HERB_ALPACA_FILE, FORMULA_ALPACA_FILE)
    entities, relations = parse_graph_data(records)

    config = Config()
    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))

    try:
        with driver.session() as session:
            if clear_first:
                print("正在清空数据库...")
                clear_database(session)

            print("正在创建索引...")
            create_indexes(session)

            print(f"准备导入 {len(entities)} 个节点、{len(relations)} 条关系")
            imported_entities = import_entities(session, entities)
            imported_relations = import_relations(session, relations)
            stats = count_graph(session)

        return {
            "records": len(records),
            "entities_prepared": len(entities),
            "relations_prepared": len(relations),
            "entities_imported": imported_entities,
            "relations_imported": imported_relations,
            "nodes_in_db": stats["nodes"],
            "relationships_in_db": stats["relationships"],
        }
    finally:
        driver.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="将 Alpaca 知识图谱数据导入 Neo4j")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="导入前清空数据库（慎用）",
    )
    args = parser.parse_args()

    try:
        stats = import_alpaca_data(clear_first=args.clear)
        print("导入完成。")
        print(f"读取 Alpaca 记录: {stats['records']} 条")
        print(f"整理节点: {stats['entities_prepared']} 个，关系: {stats['relations_prepared']} 条")
        print(f"写入节点: {stats['entities_imported']} 个，关系: {stats['relations_imported']} 条")
        print(f"数据库当前节点: {stats['nodes_in_db']} 个，关系: {stats['relationships_in_db']} 条")
        return 0
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"JSON 解析失败: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"导入失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
