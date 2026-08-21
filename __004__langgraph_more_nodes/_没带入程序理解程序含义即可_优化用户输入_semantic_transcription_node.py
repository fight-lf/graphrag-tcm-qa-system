from langchain_core.messages import HumanMessage
from __004__langgraph_more_nodes.agent_state import AgentState
from common.llm import my_llm
from common.config import Config
from langchain_core.runnables import RunnableConfig
from __005__fastapi.__03__msg_queue import put_msg_sentence_content
conf = Config()


async def semantic_transcription_node(state: AgentState, config:RunnableConfig) -> AgentState:
    """
    语义转写节点：
    根据历史对话内容（history_messages）和当前用户输入（input），
    生成一个更清晰、标准化的语义转写结果，用于下游意图识别或问题理解。
    """
    # 获取用户输入和历史上下文

    print("开始生成语义转写...")
    user_id = config.get("configurable", {}).get("thread_id")
    await put_msg_sentence_content(user_id, "开始生成语义转写...")

    user_input = state["input"]
    history_messages = state.get("history_messages", [])  # 获取历史消息,初始话空列表
    print(f"历史消息：{history_messages}")

    # 更新历史
    history_messages.append({"role": "user", "content": user_input}) # 往历史消息列表中添加用户输入
    state["history_messages"] = history_messages
    # 只保留最近5轮,历史会话记录
    history_messages = history_messages[-(conf.history_num + 1):-1]

    print("开始生成语义转写...")

    # 构建提示词
    prompt = f"""
你是一名语言理解专家，负责将用户输入转写为清晰、简洁、语义明确的问题或意图表达。
你需要基于以下上下文（最近6轮对话），分析用户真正想表达的意思。
请不要编造不存在的信息，也不要直接回答问题，只需输出语义转写后的句子。

【历史对话】
{history_messages}

【当前用户输入】
{user_input}

请输出：
1. 一句自然语言，清楚表达用户当前真正的问题或意图；
2. 不要包含解释性文字；
3. 如果用户输入含糊不清，请基于上下文合理补全语义；
4. 输出格式：直接输出转写结果，无需加前缀。
"""

    # 调用大模型
    response = my_llm.invoke([HumanMessage(content=prompt)])
    result = response.content.strip()

    # 保存语义转写结果
    state["input_semantic_trans"] = result
    print(f"完成生成语义转写：{result}")
    await put_msg_sentence_content(user_id, f"完成生成语义转写:{result}")
    return state
