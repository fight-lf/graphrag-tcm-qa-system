import faiss
import pickle
from __004__langgraph_more_nodes.agent_state import AgentState
from common.config import Config
from common.embedding_model import embedding_model

conf = Config()

# 加载索引和映射
index = faiss.read_index(conf.ENTITY_INDEX_PATH)
with open(conf.ENTITY_ID2TEXT_PATH, "rb") as f:
    id2text = pickle.load(f)


def search_faiss(query, top_k=3, threshold=0.85): # 阈值
    """
    :param query:  上一个节点抽取的用户输入数据的实体节点数据(本质上就是用户输入的信息,只是被抽取了实体,目的是为了更好的匹配neo4j里面的节点)
    :param top_k:
    :param threshold:
    :return:
    """
    """
    在已有的 FAISS 索引中搜索，并设置相似度阈值
    """
    print("开始从faiss索引搜索")

    # 生成查询向量,把用户输入的实体,转换成向量
    query_emb = embedding_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)

    # 检索 (返回 L2 距离)
    # 从本地向量库Faiss中进行检索,index来自于Faiss
    dists, ids = index.search(query_emb, top_k)

    results = []
    for j, i in enumerate(ids[0]):
        if i == -1:  # 没找到
            continue
        dist = dists[0][j]
        sim = 1.0 - dist / 2.0  # 转换成余弦相似度
        if sim >= threshold:
            results.append({"text": id2text[i], "similarity": float(sim)})
    print("完成从faiss索引搜索")
    return [result['text'] for result in results]


def match_entity_from_neo4j_node(state: AgentState) -> AgentState:
    """
        对六类实体分别在 FAISS 索引中进行匹配搜索：
        - Effect（功效）
        - Disease（疾病）
        - Symptom（症状）
        - Formula（方剂）
        - Herb（药材）
        - Source（出处）
        """
    # 获取上一节点的数据
    user_input_effects = state.get("user_input_effects", [])
    user_input_diseases = state.get("user_input_diseases", [])
    user_input_symptoms = state.get("user_input_symptoms", [])
    user_input_formulas = state.get("user_input_formulas", [])
    user_input_herbs = state.get("user_input_herbs", [])
    user_input_sources = state.get("user_input_sources", [])
    # 封装当前节点的数据,供下一个节点使用
    matched_effects, matched_diseases, matched_symptoms = [], [], []
    matched_formulas, matched_herbs, matched_sources = [], [], []

    # 分别在 FAISS 中检索
    for eff in user_input_effects:
        # 往列表里面添加检索结果
        # eff 表示功效列表里面的具体实体数据
        matched_effects.extend(search_faiss(eff)) # search_faiss(eff) 相似度匹配

    for dis in user_input_diseases:
        matched_diseases.extend(search_faiss(dis))

    for sym in user_input_symptoms:
        matched_symptoms.extend(search_faiss(sym))

    for form in user_input_formulas:
        matched_formulas.extend(search_faiss(form))

    for herb in user_input_herbs:
        matched_herbs.extend(search_faiss(herb))

    for src in user_input_sources:
        matched_sources.extend(search_faiss(src))

    # 存入 state
    state["matched_effects"] = matched_effects
    state["matched_diseases"] = matched_diseases
    state["matched_symptoms"] = matched_symptoms
    state["matched_formulas"] = matched_formulas
    state["matched_herbs"] = matched_herbs
    state["matched_sources"] = matched_sources

    print("完成实体匹配搜索")
    return state


if __name__ == '__main__':
    print(match_entity_from_neo4j_node(
        {"user_input_effects": ['补气', '止痛'], "user_input_diseases": ["感冒"], "user_input_symptoms": ['咳嗽'],
         'user_input_formulas': ['桂枝汤'],'user_input_herbs': ['人参', '黄芪']}))
