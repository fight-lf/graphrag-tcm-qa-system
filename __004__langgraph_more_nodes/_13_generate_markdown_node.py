import os

from __004__langgraph_more_nodes.agent_state import AgentState
from common.path_utils import root_dir
from langchain_core.runnables import RunnableConfig

def trans_image_path_list(image_path_list: list):
    def trans_image_path(image_path):
        relative_path = os.path.relpath(image_path, root_dir)
        return f"http://localhost:8000/{relative_path}"

    return [trans_image_path(image_path) for image_path in image_path_list]


def generate_markdown_code(title, content, image_path_list, image_width="300px", image_height="300px"):
    image_path_list = trans_image_path_list(image_path_list)
    # 创建 HTML 页面结构
    html_code = f"""
    <html>
        <head>
            <title>{title}</title>
            <style>
                .image-container {{
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                    justify-content: flex-start;
                }}
                .image-container img {{
                    width: {image_width};
                    height: {image_height};
                }}
            </style>
        </head>
        <body>
            <p>小红书发布成功</p>
            <h3>标题：{title}</h3>
            <p>内容：{content}</p>
            <div class="image-container">
    """

    # 为每张图片生成 <img> 标签
    for image_path in image_path_list:
        html_code += f'<img src="{image_path}" alt="image"/>\n'

    # 关闭 <div> 和 <body> 标签
    html_code += """</div>
        </body>
    </html>
    """
    return html_code

async def generate_markdown_node(state: AgentState):
    """根据标题和内容生成markdown"""
    title = state.get('xiaohongshu_tcm_post_title')
    content = state.get('xiaohongshu_tcm_post_content')
    image_path_list = state.get('xiaohongshu_image_path_list')
    markdown = generate_markdown_code(title, content, image_path_list)
    state['xiaohongshu_markdown_output'] = markdown
    state['output'] = markdown
    return state

if __name__ == '__main__':
    print(generate_markdown_code("标题", "内容",
                                 [r"D:\workspace\workspace_python\k_graph_2\picture\20260608171356南京3日游.png"]))
