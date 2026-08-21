from __004__langgraph_more_nodes.agent_state import AgentState
from common.neo4j_manager import neo4j_client
from langchain_core.runnables import RunnableConfig

def run_cypher_node(state: AgentState):
    print("开始运行大模型cypher语句")
    cypher_query_list = state.get("cypher_query", [])
    query_results = []

    for cypher_query in cypher_query_list:
        result_list = neo4j_client.run_cypher(cypher_query)
        query_results.append({
            "query": cypher_query,
            "result": result_list
        })

    # 存入 state
    state["cypher_results"] = query_results
    print("完成运行大模型cypher语句")
    return state

if __name__ == '__main__':
    ls_cypher = [
        "MATCH (d:Disease)-[:TREATS_DISEASE]-(f:Formula) WHERE d.name IN ['四时感冒', '感冒咳嗽', '感冒风寒'] RETURN DISTINCT f.name AS formula, f.indication AS indication, f.effect AS effect",
        "MATCH (d:Disease)-[:HAS_SYMPTOM]-(s:Symptom) WHERE d.name IN ['四时感冒', '感冒咳嗽', '感冒风寒'] RETURN DISTINCT d.name AS disease, collect(s.name) AS symptoms",
        "MATCH (f:Formula)-[:TREATS_DISEASE]->(d:Disease) WHERE d.name IN ['四时感冒', '感冒咳嗽', '感冒风寒'] MATCH (f)-[:HAS_INGREDIENT]->(h:Herb) RETURN f.name AS formula, collect(h.name) AS herbs",
        "MATCH (d:Disease) WHERE d.name IN ['四时感冒', '感冒咳嗽', '感冒风寒'] MATCH (d)<-[:TREATS_DISEASE]-(h:Herb) RETURN d.name AS disease, collect(h.name) AS treating_herbs"
    ]


    # print(run_cypher_node({"cypher_query":[" MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom) WHERE d.name IN ['四时感冒', '感冒风邪', '咳嗽'] RETURN d.name AS disease, s.name AS symptom"]}))
    print(run_cypher_node({"cypher_query":ls_cypher}))
