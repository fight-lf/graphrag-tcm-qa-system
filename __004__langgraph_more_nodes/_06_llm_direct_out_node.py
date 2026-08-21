from __004__langgraph_more_nodes.agent_state import AgentState
from langchain_core.messages import HumanMessage
from common.llm import my_llm
from langgraph.types import RunnableConfig
import asyncio

async def llm_direct_out_node(state: AgentState,config:RunnableConfig = None):
    print("开始生成直接用户回答")

    # 获取用户输入
    user_input = state["input"]

    # 构建提示词（专注中医回答）
    prompt = f"""
    用户输入: {user_input}

    你是一名专业的中医知识助手，回答时请尽量基于中医理论和术语来解释。
    要求：
    - 优先从中医角度（如症状、方剂、中药材、功效、经络、辨证论治、典籍等）进行回答。
    - 如果问题与中医无关，请直接给出简洁的常规回答，不要强行套用中医。
    - 回答要准确、简洁，避免无关内容。
    - 输出时只给出最终答案，不要解释你是如何推理的。
    """

    # 调用大模型
    # response = my_llm.invoke([HumanMessage(content=prompt)])
    # model_answer = response.content.strip()
    result = ""
    for chunk in my_llm.stream([HumanMessage(content=prompt)]):
        result += chunk.content
        print(chunk.content,end="",flush=True)
    model_answer = result.strip()

    history_messages = state.get("history_messages", [])
    history_messages.append({"role": "assistant", "content": model_answer})
    state["history_messages"] = history_messages

    # 存入 state
    state["direct_out"] = model_answer
    state["output"] = model_answer
    print("完成生成直接用户回答")
    return state

if __name__ == '__main__':
    result = asyncio.run(llm_direct_out_node({'input':'武术技能如何提高'}))
    print(result)
