from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import List, Optional, Union, Literal
from langchain_core.prompts import PromptTemplate
import os
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.llm import my_llm
from common.path_utils import get_file_path

# ======================
# 枚举定义: 实体 ，Literal是一种特殊类型，python3.8引入了Literal类型
# ======================

'''
    此代码脚本的功能：
      1. 抽取方剂和药材的实体和关系
      2. 需要生成json文件
      3. 是为最终转成AIpaca格式做铺垫，AIpaca格式是指令微调的标准格式，这种格式的好处，是让大模型严格按照用户的需求生成结果

    开发步骤：
       1. 需要写两个脚本，分别抽取中药和方剂的文本数据，并存储为2个json格式文件
       2. 再写一个代码，基于上一步的抽取结果，把数据转成AIpaca格式文件

'''

EntityType = Literal["Symptom", "Disease", "Formula", "Herb", "Effect", "Source"] # 强约束：严格限制变量只能取指定的几个固定字符串值之一

# 关系
RelationType = Literal[
    "TREATS_DISEASE",
    "ALLEVIATES_SYMPTOM",
    "HAS_EFFECT",
    "HAS_INGREDIENT",
    "HAS_SYMPTOM",
    "FROM_SOURCE"
]


# ======================
# 方剂属性定义
# ======================
class FormulaAttributes(BaseModel): # BaseModel 属于pydantic的基类，用于定义数据模型，定义了数据结构，以及数据验证和转换。
    alias: Optional[str] = None # Optional 表示可选，默认值为None
    effect: Optional[str] = None  # 方剂具有的主要功效
    indication: Optional[str] = None  # 适应症或主治病证
    taboo: Optional[str] = None # 禁忌或使用限制
    usage: Optional[str] = None # 服用方法和剂型

# 药材属性定义
class HerbAttributes(BaseModel):
    dosage: Optional[str] = None
    effect: Optional[str] = None
    indication: Optional[str] = None
    meridian: Optional[str] = None
    origin: Optional[str] = None
    place: Optional[str] = None
    processing: Optional[str] = None
    property_flavor: Optional[str] = None
    taboo: Optional[str] = None
    traits: Optional[str] = None


# ======================
# 实体与关系结构
# ======================
class Entity(BaseModel):
    name: str
    type: EntityType
    attributes: Optional[Union[FormulaAttributes, HerbAttributes]] = None

# 关系
class Relation(BaseModel):
    subject: str            # 一个实体
    subject_type: EntityType
    relation: RelationType  # 关系
    object: str             # 指向另一个实体
    object_type: EntityType

# 确定实体和关系
class TCMKnowledgeGraph(BaseModel):
    entities: List[Entity]
    relations: List[Relation]


# 初始化解析器
parser = JsonOutputParser(pydantic_object=TCMKnowledgeGraph)

# 定义 Prompt
prompt = PromptTemplate(
    template=(
        "你是一个中医知识图谱抽取专家。请从以下文本中提取结构化知识：\n"
        "仅当文本中存在实体之间的明确关系时（如‘某方剂治疗某疾病’、‘某药材具有某功效’、‘方剂包含药材’等），才进行抽取。\n"
        "如果文本中仅描述单个实体的信息、未涉及其他实体或关系，请不要抽取，返回空结构：\n"
        "{{\"entities\": [], \"relations\": []}}\n\n"

        "【实体类型说明】\n"
        "- Symptom：症状，如咳嗽、腹痛等\n"
        "- Disease：疾病，如感冒、肺炎、肾虚等\n"
        "- Formula：方剂，如四君子汤、桂枝汤等\n"
        "- Herb：药材，如人参、黄芪、丁香等\n"
        "- Effect：功效，如补气、活血、祛湿、止痛等\n"
        "- Source：出处，如《本草纲目》《伤寒论》等\n\n"

        "【关系类型说明】\n"
        "- TREATS_DISEASE：方剂或药材治疗某种疾病\n"
        "- ALLEVIATES_SYMPTOM：方剂或药材缓解某种症状\n"
        "- HAS_EFFECT：方剂或药材具有某种功效\n"
        "- HAS_INGREDIENT：方剂包含某种药材\n"
        "- HAS_SYMPTOM：疾病包含某种症状\n"
        "- FROM_SOURCE：方剂出自某文献或出处\n\n"

        "若文本涉及方剂或药材，请补充对应的属性字段（如功效、性味、剂量等）。\n"
        "如果文本主要是讲方剂的，请不要抽取药材的属性字段。\n"
        "如果文本主要是讲药材的，请不要抽取方剂的属性字段。\n"
        "如果值为空null，则不必显示键的值。"
        "所有输出必须严格符合以下 JSON 格式：\n"
        "{format_instructions}\n\n"
        "输入文本：{text}"
    ),
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# ======================
# 主函数封装
# ======================
def extract_tcm_knowledge(text: str):
    # 构建抽取链,提示链
    chain = prompt | my_llm | parser
    return chain.invoke({"text": text})

def _to_json_serializable(data):
    if hasattr(data, "model_dump"):
        return data.model_dump()
    return data

if __name__ == '__main__':

    text = '''
        名称
        东南长蒴苣苔、石麻婆子草、石茶

        东南长蒴苣苔的种植和炮制
        来源
        为苦苣苔科植物东南长蒴苣苔的全草。春季采收，晒干。
        【原形态】
        东南长蒴苣苔，多年生草本。根状茎圆柱形，长约4cm。叶4-16，均基生；叶柄长1.8-8cm，粗壮，有短糙毛；叶片纸质，长圆形或长圆状椭圆形，有2.2-10cm，宽1-3.6cm，先端急尖或微尖，基部楔形，边缘密小牙齿，两侧均被短伏毛，侧脉每侧5-7条。聚伞花序状，2-4条，2-3回分枝，第短伏毛；花萼长4.5-7mm，5裂达基部，裂片狭线形，外面被短伏毛，内面无毛；花冠长1.5-2cm，外面被短柔毛，内面近无毛，简狭钟状，上唇长3-5mm，2裂至中部，裂片斜扁三角形，下唇3裂至中部，裂片卵形；雄蕊无毛，花药椭圆形，退化雄蕊2，长约0.5mm；花盘环状；雌蕊长约1.6cm，疏被小腺体；子房无柄，柱头扁球形。蒴果线形，长2-3.4cm，无毛。种子狭窄椭圆形或纺锤形，长0.4-0.5mm。花期4月左右。
        【生境分布】
        生态环境：生于山谷林下或山坡石上或石崖上。
        资源分布：分布于江西、福建、湖南、广东等地。
        性味
        味苦；辛；性凉

        东南长蒴苣苔的效果
        功效
        为苦苣苔科植物东南长蒴苣苔的全草。主治感受风热，鼻塞流涕，喷嚏，咳嗽。
        主治
        散风热解毒。主感受风热，鼻塞流涕，喷嚏，咳嗽。
        用法用量
        内服：煎汤，6-9g。
    '''

    knowledge = extract_tcm_knowledge(text)
    print(knowledge)
