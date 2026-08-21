from __004__langgraph_more_nodes.agent_state import AgentState
from langchain_core.messages import HumanMessage
from common.llm import my_llm
import json
from langchain_core.runnables import RunnableConfig

def neo4j_answer_generate_node(state: AgentState) -> AgentState:
    print("开始进行neo4j输入大模型的回答")
    user_input = state["input"] # 用户输入
    cypher_results = state.get("cypher_results", []) # neo4j的查询结果

    # 把 cypher_results 转成字符串，方便喂给大模型
    # 转成json字符串
    cypher_results_str = json.dumps(cypher_results, ensure_ascii=False, indent=2)

    prompt = f"""
    你是一个中医知识图谱问答助手。
    用户提出了问题：{user_input}

    我已经在 Neo4j 图数据库中执行了查询，查询结果如下：
    {cypher_results_str}

    请你根据这些查询结果，用简洁、清晰、自然的中文回答用户的问题。
    如果查询结果无法回答用户的问题，请如实告知用户没有找到相关答案。
    """
    # print(prompt)
    response = my_llm.invoke([HumanMessage(content=prompt)])

    history_messages = state.get("history_messages", [])
    history_messages.append({"role": "assistant", "content": response.content.strip()})
    state["history_messages"] = history_messages

    # 保存结果
    answer = response.content.strip()
    state["neo4j_answer"] = answer
    state["output"] = answer
    print("完成进行neo4j输入大模型的回答")
    # 推送最终回复给前端，否则流式页面收不到回复内容
    return state

if __name__ == '__main__':

    print(neo4j_answer_generate_node({"input": "四时感冒是什么病？", "cypher_results": [{'query': " MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom) WHERE d.name IN ['四时感冒', '感冒风邪', '咳嗽'] RETURN d.name AS disease, s.name AS symptom", 'result': [{'disease': '四时感冒', 'symptom': '身体疼痛'}, {'disease': '四时感冒', 'symptom': '头痛'}, {'disease': '四时感冒', 'symptom': '项强'}, {'disease': '四时感冒', 'symptom': '流涕'}, {'disease': '四时感冒', 'symptom': '恶风'}, {'disease': '四时感冒', 'symptom': '胸脘痞闷'}, {'disease': '四时感冒', 'symptom': '恶寒'}, {'disease': '四时感冒', 'symptom': '发热'}, {'disease': '四时感冒', 'symptom': '无汗'}, {'disease': '四时感冒', 'symptom': '鼻塞'}]}]}))
