import asyncio
import json
from __004__langgraph_more_nodes.agent_state import AgentState
from common.config import Config
from langchain_core.messages import HumanMessage
from common.llm import my_llm
from langchain_core.runnables import RunnableConfig
conf = Config()


async def generate_neo4j_cypher_node(state: AgentState) -> AgentState:
    print("开始生成neo4j的cypher语句")

    user_input = state["input"]

    # 从 state 取出所有匹配到的实体
    matched_effects = state.get("matched_effects", [])
    matched_diseases = state.get("matched_diseases", [])
    matched_symptoms = state.get("matched_symptoms", [])
    matched_formulas = state.get("matched_formulas", [])
    matched_herbs = state.get("matched_herbs", [])
    matched_sources = state.get("matched_sources", [])

    meta_data = conf.TCM_METADATA  # 知识图谱元数据（节点、关系定义等）

    # 格式化匹配到的实体，确保只保留文本内容
    def format_entities(entities):
        if isinstance(entities, list): # 类型匹配
            return [e["text"] if isinstance(e, dict) else str(e) for e in entities]
        return []

    effects_list = format_entities(matched_effects)
    diseases_list = format_entities(matched_diseases)
    symptoms_list = format_entities(matched_symptoms)
    formulas_list = format_entities(matched_formulas)
    herbs_list = format_entities(matched_herbs)
    sources_list = format_entities(matched_sources)

    # 构建提示词
    prompt = f"""
    你是一个 Neo4j Cypher 查询语句生成助手。
    请基于中医知识图谱，结合用户输入和已匹配实体，生成最合适的查询语句。

    用户输入：{user_input}

    匹配到的实体：
    - effects（功效）: {effects_list}
    - diseases（疾病）: {diseases_list}
    - symptoms（症状）: {symptoms_list}
    - formulas（方剂）: {formulas_list}
    - herbs（药材）: {herbs_list}
    - sources（出处）: {sources_list}

    知识图谱元数据（节点与关系定义）：
    {meta_data}

    要求：
    1. 根据用户输入语义、匹配到的实体及元数据，生成 1~N 条合适的 Cypher 查询。
    2. 输出必须是严格的 JSON 格式：
    {{
        "cypher": [
            "MATCH ... RETURN ...",
            "MATCH ... RETURN ..."
        ]
    }}
    3. 不得包含任何解释或额外文字。
    """

    # 调用大模型
    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    try:
        cypher_data = json.loads(raw_output)
    except json.JSONDecodeError:
        cypher_data = {"cypher": []}

    # 保存结果到 state
    state["cypher_query"] = cypher_data.get("cypher", [])

    print(f"完成生成neo4j的cypher语句{state['cypher_query']}")
    return state

if __name__ == '__main__':
    # {'user_input_effects': ['补气', '止痛'], 'user_input_diseases': ['感冒'], 'user_input_symptoms': ['咳嗽'],
    #  'user_input_formulas': ['桂枝汤'], 'user_input_herbs': ['人参', '黄芪'], 'matched_effects': ['补气', '止痛'],
    #  'matched_diseases': ['感冒', '感冒咳嗽', '感冒风寒'], 'matched_symptoms': ['咳嗽', '感冒咳嗽', '咳'],
    #  'matched_formulas': ['桂枝汤', '桂枝加桂汤', '桂枝新加汤'], 'matched_herbs': ['人参', '黄芩', '黄芪'],
    #  'matched_sources': []}

    result = asyncio.run(generate_neo4j_cypher_node({'input':'感冒,咳嗽,风寒','matched_diseases': ['四时感冒', '感冒咳嗽', '感冒风寒']}))
    print(result)
