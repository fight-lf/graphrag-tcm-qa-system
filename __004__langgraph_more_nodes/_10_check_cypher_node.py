import asyncio

from __004__langgraph_more_nodes.agent_state import AgentState
from common.neo4j_manager import neo4j_client
from langchain_core.runnables import RunnableConfig

async def check_cypher_node(state:AgentState):
    print("开始检查cypher语句")
    cypher_query_list = state["cypher_query"]  # 获取上一个节点的查询语句
    state['is_all_validate_cypher'] = True # 默认为True
    for cypher_query in cypher_query_list:
        if not neo4j_client.validate_cypher(cypher_query):
            state['is_all_validate_cypher'] = False
            break
    print(f"完成检查cypher语句:{state['is_all_validate_cypher']}")
    return state

def validate_cypher(self, query: str) -> bool:
    """
    检测 Cypher 查询语句是否合法（语法层面）
    :param query: 待检测的 Cypher 语句
    :return: True 表示合法，False 表示不合法
    """
    try:
        with self.driver.session() as session:
            # 使用 EXPLAIN 只做解析，不执行
            session.run(f"EXPLAIN {query}")
        return True
    except Exception as e:
        print(f"Cypher 语法错误: {e}")
        return False

if __name__ == '__main__':
    ls_cypher = [
                 "MATCH (d:Disease)-[:TREATS_DISEASE]-(f:Formula) WHERE d.name IN ['四时感冒', '感冒咳嗽', '感冒风寒'] RETURN DISTINCT f.name AS formula, f.indication AS indication, f.effect AS effect",
                 "MATCH (d:Disease)-[:HAS_SYMPTOM]-(s:Symptom) WHERE d.name IN ['四时感冒', '感冒咳嗽', '感冒风寒'] RETURN DISTINCT d.name AS disease, collect(s.name) AS symptoms",
                 "MATCH (f:Formula)-[:TREATS_DISEASE]->(d:Disease) WHERE d.name IN ['四时感冒', '感冒咳嗽', '感冒风寒'] MATCH (f)-[:HAS_INGREDIENT]->(h:Herb) RETURN f.name AS formula, collect(h.name) AS herbs",
                 "MATCH (d:Disease) WHERE d.name IN ['四时感冒', '感冒咳嗽', '感冒风寒'] MATCH (d)<-[:TREATS_DISEASE]-(h:Herb) RETURN d.name AS disease, collect(h.name) AS treating_herbs"
               ]

    # result = asyncio.run(check_cypher_node({"cypher_query": ["MATCH (e:Employee) RETURN e.id, e.name, e.salary, e.deptno"]}))
    result = asyncio.run(check_cypher_node({"cypher_query": ls_cypher}))
    print()
