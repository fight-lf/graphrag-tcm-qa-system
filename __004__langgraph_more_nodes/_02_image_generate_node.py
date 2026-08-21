import os
import requests

import datetime

from volcengine.visual.VisualService import VisualService
from __004__langgraph_more_nodes.agent_state import AgentState
from common.config import Config
from common.path_utils import get_file_path

conf = Config()

def sanitize_title_for_filename(title: str, max_length: int = 10) -> str:
    """
    将标题字符串清洗成适合作为文件名的格式（去除不合法字符，只保留前max_length个字符）
    :param title: 原始标题
    :param max_length: 截取的最大字符数
    :return: 清洗后的文件名部分
    """
    # 获取现在的时间
    now = datetime.datetime.now()
    # 格式化时间
    time_str = now.strftime("%Y%m%d%H%M%S")
    return time_str + title[:5] + ".png"

# 设置提示词 -> 生图
def generate_jimeng_prompt(title: str, content: str) -> str:
    return (
        f"一幅围绕中医养生主题创作的图像，画面展现与标题内容相关的场景，"
        f"构图中包含人物或物品与养生行为（如冥想、泡脚、煮药、食疗、经络按摩等），"
        f"整体氛围温和、宁静、有疗愈感，色调自然柔和，背景可融入自然或居家环境，"
        f"表达健康、平衡与舒缓的情绪。"
        f"图片主题为:{title},"
        f"图片内容为:{content},"
        f"图片中不能有任何文字。"
        f"整体画面和谐、美观，符合图片质量要求。"
        f"图片中包含与中医养生主题相关的元素，如中药、穴位、食物、运动等。"
        f"文字与画面协调，不影响整体美感。允许画风自由表达，可现代、写意、插画、水彩或其他形式。"
    )

def download_image_from_url(url: str, output_path: str):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)
        print(f"图片已保存：{output_path}")
    except requests.exceptions.RequestException as e:
        print(f"下载失败：{e}")

def generate_image(prompt: str, output_path: str):
    visual_service = VisualService()
    visual_service.set_ak(conf.JIMENG_AK)  # 替换为你自己的 AK
    visual_service.set_sk(conf.JIMENG_SK)  # 替换为你自己的 SK

    form = {
        "req_key": "jimeng_high_aes_general_v21_L",
        "prompt": prompt,
        "return_url": True
    }

    resp = visual_service.cv_process(form)
    image_urls = resp.get('data', {}).get('image_urls', [])
    if image_urls:
        download_image_from_url(image_urls[0], output_path)
        return output_path
    else:
        raise RuntimeError("图像生成失败，无有效图片链接返回")

def xiaohongshu_image_generator(title, content):
    # 生成提示词
    prompt = generate_jimeng_prompt(title, content)

    # 建了一个文件夹，用于保存图片
    os.makedirs(get_file_path("picture"), exist_ok=True)
    file_name = sanitize_title_for_filename(title) # 生成文件名(图片)
    output_path = os.path.join(get_file_path("picture"), file_name) # 图片保存路径

    image_path = generate_image(prompt, output_path)
    return image_path

# 流程图的一部分,所以需要获取上一个节点的数据,并封装返回下一个节点所需要的数据
def image_generator_node(state: AgentState):
    try:
        """根据标题和内容生成中医养生风格的小红书配图"""
        print("开始生成小红书图片生成")
        title = state.get('xiaohongshu_tcm_post_title')
        content = state.get('xiaohongshu_tcm_post_content')

        image_path = xiaohongshu_image_generator(title, content)

        state['xiaohongshu_image_path_list'] = [image_path]
        print(f"图片生成成功: {image_path}")
        state['xiaohongshu_tcm_tip'] = "图片生成成功"
        print("完成生成小红书图片生成")
        return state
    except Exception as e:
        import traceback
        traceback.print_exc()
        return state

if __name__ == '__main__':
    xiaohongshu_image_generator("洗脚有什么好处呢？", "很多好处")
