import asyncio
from __004__langgraph_more_nodes.agent_state import AgentState
from langchain_core.messages import HumanMessage
from common.llm import my_llm
from langchain_core.runnables import RunnableConfig

async def xiaohongshu_publish_intent_node(state: AgentState):
    print("开始识别是否有发小红书的意图识别")
    # 获取用户输入
    user_input = state["input"]

    # 构建提示词，强制模型只输出“是”或“否”
    prompt = f"""
    用户输入: {user_input}

    你是一个意图分类器。
    任务：判断用户是否有“要在小红书发笔记/发内容”的意图。
    输出要求：只能输出“是”或“否”，不要输出任何解释或其他文字。
    """

    # 调用大模型
    response = my_llm.invoke([HumanMessage(content=prompt)])
    model_answer = response.content.strip()

    # 严格校验输出，只认“是”或“否”
    if model_answer == "是":
        state["is_xiaohongshu_publish_intent"] = True
    elif model_answer == "否":
        state["is_xiaohongshu_publish_intent"] = False
    else:
        # 防御性处理：如果模型乱输出，默认认为“否”
        state["is_xiaohongshu_publish_intent"] = False
    print("完成识别是否有发小红书的意图识别")

    return state

if __name__ == '__main__':
    result = asyncio.run(xiaohongshu_publish_intent_node({'input': '小红书发布生姜药材'}))
    print(result)
