from typing import TypedDict, List


class AgentState(TypedDict):
    # 输入
    input: str
    # 输入的语义转写结果
    input_semantic_trans: str
    # 判断是否有发小红书的意图
    is_xiaohongshu_publish_intent: bool
    # 生成小红书标题和正文
    xiaohongshu_tcm_post_title: str
    xiaohongshu_tcm_post_content: str
    # 生成小红书图片
    xiaohongshu_image_path_list: [str]
    xiaohongshu_tcm_tip: str
    # 是否可以发布小红书
    is_can_publish_xiaohongshu: bool
    # 小红书markdown输出结果
    xiaohongshu_markdown_output: str
    # 是否跟中医有关系
    is_zhongyi_intent: bool
    # 直接回答
    direct_out: str
    # 用户输入的实体抽取
    user_input_effects: List[str]
    user_input_diseases: List[str]
    user_input_symptoms: List[str]
    user_input_formulas: List[str]
    user_input_herbs: List[str]
    user_input_sources: List[str]
    # 匹配的实体
    matched_effects: List[str]
    matched_diseases: List[str]
    matched_symptoms: List[str]
    matched_formulas: List[str]
    matched_herbs: List[str]
    matched_sources: List[str]
    # cypher查询语句
    cypher_query: List[str]
    is_all_validate_cypher: bool
    cypher_results: List[...]
    neo4j_answer: str
    # 添加记忆
    history_messages: List[dict]

    # 输出
    output: str
