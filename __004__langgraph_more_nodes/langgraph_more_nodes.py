from langgraph.constants import START, END
from langgraph.graph import StateGraph

from __004__langgraph_more_nodes.agent_state import AgentState

from __004__langgraph_more_nodes.nodes2._00_xiaohongshu_publish_intent_node import  xiaohongshu_publish_intent_node
from __004__langgraph_more_nodes.nodes2._01_text_generate_node import text_generate_node
from __004__langgraph_more_nodes.nodes2._02_image_generate_node import image_generator_node
from __004__langgraph_more_nodes.nodes2._03_check_text_image_node import check_text_image_node
from __004__langgraph_more_nodes.nodes2._04_auto_publish_xiaohongshu_node import xiaohongshu_auto_publish_node
from __004__langgraph_more_nodes.nodes2._05_zhongyi_intent_node import zhongyi_intent_node
from __004__langgraph_more_nodes.nodes2._06_llm_direct_out_node import llm_direct_out_node
from __004__langgraph_more_nodes.nodes2._07_extract_entity_from_user_input_node import extract_entity_from_user_input_node
from __004__langgraph_more_nodes.nodes2._08_match_entity_from_neo4j_node import match_entity_from_neo4j_node
from __004__langgraph_more_nodes.nodes2._09_generate_neo4j_cypher_node import generate_neo4j_cypher_node
from __004__langgraph_more_nodes.nodes2._10_check_cypher_node import check_cypher_node
from __004__langgraph_more_nodes.nodes2._11_run_cypher_node import run_cypher_node
from __004__langgraph_more_nodes.nodes2._12_neo4j_answer_generate_node import neo4j_answer_generate_node
from __004__langgraph_more_nodes.nodes2._13_generate_markdown_node import generate_markdown_node

'''
  中医知识图谱流程讲解：
     1. 图的构建（图的执行流程）
     2. 链路1： 小红书自动发布
     3. 链路2： 中医知识检索GraphRAG
'''


# 构建状态图
def build_graph():
    # 定义状态图
    graph = StateGraph(AgentState)

    # 共14个节点(函数)
    graph.add_node(xiaohongshu_publish_intent_node.__name__, xiaohongshu_publish_intent_node) # __name__ 获取函数名 ,这种获取函数名称是推荐写法,便于后续的维护
    graph.add_node(text_generate_node.__name__, text_generate_node)
    graph.add_node(image_generator_node.__name__, image_generator_node)
    graph.add_node(xiaohongshu_auto_publish_node.__name__, xiaohongshu_auto_publish_node)
    graph.add_node(zhongyi_intent_node.__name__, zhongyi_intent_node)
    graph.add_node(llm_direct_out_node.__name__, llm_direct_out_node)
    graph.add_node(extract_entity_from_user_input_node.__name__, extract_entity_from_user_input_node)
    graph.add_node(match_entity_from_neo4j_node.__name__, match_entity_from_neo4j_node)
    graph.add_node(generate_neo4j_cypher_node.__name__, generate_neo4j_cypher_node)
    graph.add_node(check_cypher_node.__name__, check_cypher_node)
    graph.add_node(run_cypher_node.__name__, run_cypher_node)
    graph.add_node(neo4j_answer_generate_node.__name__, neo4j_answer_generate_node)
    graph.add_node(check_text_image_node.__name__, check_text_image_node)
    graph.add_node(generate_markdown_node.__name__, generate_markdown_node)

    # 添加边,添加起点
    graph.add_edge(START, xiaohongshu_publish_intent_node.__name__)

    # 条件判断
    def is_xiaohongshu_publish_intent_condition(state: AgentState):
        if state['is_xiaohongshu_publish_intent']:
            return text_generate_node.__name__ # 发布小红书的分支
        else:
            return zhongyi_intent_node.__name__ # 中医的分支

    # 添加条件边,条件判断,分支选择
    graph.add_conditional_edges(xiaohongshu_publish_intent_node.__name__, is_xiaohongshu_publish_intent_condition,
                                path_map={
                                    text_generate_node.__name__: text_generate_node.__name__,
                                    zhongyi_intent_node.__name__: zhongyi_intent_node.__name__
                                })
    '''
        中医意图识别
    '''
    def is_zhongyi_intent_condition(state: AgentState):
        if state['is_zhongyi_intent']:
            return extract_entity_from_user_input_node.__name__
        else:
            return llm_direct_out_node.__name__

    graph.add_conditional_edges(zhongyi_intent_node.__name__, is_zhongyi_intent_condition,
                                path_map={
                                    extract_entity_from_user_input_node.__name__: extract_entity_from_user_input_node.__name__,
                                    llm_direct_out_node.__name__: llm_direct_out_node.__name__
                                })
    # 如果是直接大模型输出
    graph.add_edge(llm_direct_out_node.__name__, END)

    graph.add_edge(extract_entity_from_user_input_node.__name__, match_entity_from_neo4j_node.__name__)
    graph.add_edge(match_entity_from_neo4j_node.__name__, generate_neo4j_cypher_node.__name__)
    graph.add_edge(generate_neo4j_cypher_node.__name__, check_cypher_node.__name__)

    def is_all_validate_cypher_condition(state: AgentState): # 检测cypher语句是否合法
        if state['is_all_validate_cypher']:
            return run_cypher_node.__name__
        else:
            return generate_neo4j_cypher_node.__name__

    graph.add_conditional_edges(check_cypher_node.__name__, is_all_validate_cypher_condition,
                                path_map={
                                    run_cypher_node.__name__: run_cypher_node.__name__,
                                    generate_neo4j_cypher_node.__name__: generate_neo4j_cypher_node.__name__
                                }
                                )
    graph.add_edge(run_cypher_node.__name__, neo4j_answer_generate_node.__name__)
    graph.add_edge(neo4j_answer_generate_node.__name__, END)


    '''
        发布小红书
    '''
    graph.add_edge(text_generate_node.__name__, image_generator_node.__name__)
    graph.add_edge(image_generator_node.__name__, check_text_image_node.__name__)

    def is_check_text_image_condition(state: AgentState):
        if state['is_can_publish_xiaohongshu']:
            return xiaohongshu_auto_publish_node.__name__
        else:
            return END

    graph.add_conditional_edges(check_text_image_node.__name__, is_check_text_image_condition, path_map={
        xiaohongshu_auto_publish_node.__name__: xiaohongshu_auto_publish_node.__name__,
        END: END
    })
    graph.add_edge(xiaohongshu_auto_publish_node.__name__, generate_markdown_node.__name__)
    graph.add_edge(generate_markdown_node.__name__, END)

    # 编译状态图
    from langgraph.checkpoint.memory import InMemorySaver
    memory = InMemorySaver()  # 添加记忆功能->内存记录会话
    app = graph.compile(memory)
    return app

app = build_graph()
# 输出表的状态图
# output_pic_graph(app, get_file_path("__004__langgraph_more_nodes/graph.jpg"))

async def zhongyi_response(input: str,user_id:str):
    # config = RunnableConfig(
    #     configurable={'thread_id':user_id}
    # )
    config = {
        "configurable": {
            "thread_id": user_id
        }
    }
    result = await app.ainvoke({"input": input},config = config)
    return result["output"]

def main():
    """测试样例：运行图并打印输出。"""
    import asyncio
    # 样例1：中医意图（可走 Neo4j 检索分支）
    # test_input = "杏仁有什么功效？"
    # # test_input = "感染风寒了,吃什么药呢？？"
    # print(f"输入: {test_input}")
    # result = asyncio.run(zhongyi_response(test_input,"user_001"))
    # print(f"输出: {result}")
    # print("-" * 40)

    # 样例2：非中医意图（走直接回答分支）
    test_input2 = "把大青龙汤的妙用,发布小红书？"
    print(f"输入: {test_input2}")
    result = asyncio.run(zhongyi_response(test_input2,"user_001"))
    print(f"输出: {result}")


if __name__ == "__main__":
    main()
