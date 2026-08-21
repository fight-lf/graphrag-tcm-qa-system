# 基于 GraphRAG 的中医药问答系统

面向中医药知识的 GraphRAG 项目，覆盖数据采集与清洗、知识抽取、Neo4j 图谱构建、实体向量匹配、Cypher 生成与校验，以及基于 LangGraph 的多节点问答编排。

## 核心流程

```text
网页采集 → 文本清洗 → 实体/关系抽取 → Neo4j 图谱导入
       → 用户意图识别 → 实体匹配 → Cypher 生成与校验
       → 图谱查询 → 答案生成 → FastAPI/Streamlit 输出
```

## 项目结构

```text
__001__crawler/               # 中药与方剂网页采集、文本格式化
__002__extract_information/   # 实体关系抽取与 Alpaca 格式转换
__003__create_neo4j_database/ # Neo4j 导入、元数据和 FAISS 索引
__004__langgraph_more_nodes/  # LangGraph 多节点业务编排
__005__fastapi/               # 流式与非流式 API
__006__streamlit/             # 对话界面
common/                       # 模型、配置、Neo4j 与路径工具
```

## 快速开始

```bash
python -m venv .venv
pip install -r requirements.txt
```

复制 `.env.example` 为 `.env`，填写模型服务、Neo4j 和本地嵌入模型路径。完成知识图谱和向量索引准备后，可分别启动 FastAPI 与 Streamlit 服务。

## 数据与安全说明

本仓库不包含采集结果、原始/处理后数据集、知识图谱导出、向量索引、本地模型权重、生成图片或任何真实凭据，仅保留数据清洗、知识抽取、图谱构建与问答编排的实现代码。
