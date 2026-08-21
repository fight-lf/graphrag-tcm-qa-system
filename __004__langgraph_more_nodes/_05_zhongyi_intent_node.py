import asyncio

from __004__langgraph_more_nodes.agent_state import AgentState
from langchain_core.messages import HumanMessage
from common.llm import my_llm
from langchain_core.runnables import RunnableConfig

async def zhongyi_intent_node(state: AgentState):
    print("开始识别是否是中医的意图识别")
    # 获取用户输入
    user_input = state["input"]
    history_messages = state.get("history_messages", [])
    history_messages.append({"role": "user", "content": user_input})
    state["history_messages"] = history_messages

    # 构建提示词：只允许输出“是”或“否”
    prompt = f"""
    用户输入: {user_input}

    你是一个意图分类器。
    请根据下列知识图谱的范围，判断该输入是否与中医相关：

    【中医知识图谱范围】
    - **症状 (Symptom)**：如咳嗽、腹泻、发热
    - **中药材 (Herb)**：包括药材的名称、别名、性味、功效、归经、禁忌、产地、炮制方法等
    - **方剂 (Formula)**：包括方剂名称、别名、功效、组成药材、适应症、来源书籍、用法等
    - **功效分类 (EffectCategory / Effect)**：如祛湿、补气、清热、活血等
    - **方剂分类 (FormulaCategory)**：如清热剂、补益剂、攻下剂等
    - **疾病 (Disease)**：如风寒感冒、脾虚泄泻等
    - **药性/药味/归经 (HerbNature / HerbFlavor / Meridian)**：寒热温凉平，甘苦辛咸酸淡，肺经、肝经等
    - **典籍来源 (Source)**：如《伤寒论》《本草纲目》

    【任务要求】
    - 如果用户输入内容中涉及到上述任意节点或关系（如问中药、方剂、症状、功效、疾病、经络、典籍等），则判定为“是”。
    - 如果用户输入内容完全与上述图谱无关（例如纯粹的数学题、娱乐话题、现代西医知识等），则判定为“否”。

    【输出要求】
    - 只能输出“是”或“否”，不要输出任何解释或其他文字。
    """

    # 调用大模型
    response = my_llm.invoke([HumanMessage(content=prompt)])
    model_answer = response.content.strip()

    # 严格判断输出
    if model_answer == "是":
        state["is_zhongyi_intent"] = True
    elif model_answer == "否":
        state["is_zhongyi_intent"] = False
    else:
        # 防御性兜底：如果大模型不守规矩，就当成“否”
        state["is_zhongyi_intent"] = False
    print("完成识别是否是中医的意图识别")

    return state

if __name__ == '__main__':
    result = asyncio.run(zhongyi_intent_node({'input':'武术技能如何提高'}))
    print(result)
