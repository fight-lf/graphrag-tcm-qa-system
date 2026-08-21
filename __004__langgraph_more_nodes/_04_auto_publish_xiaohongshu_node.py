from playwright.async_api import async_playwright
import os
import asyncio

from __004__langgraph_more_nodes.agent_state import AgentState
from common.path_utils import get_file_path
from langchain_core.runnables import RunnableConfig

# 主要是发布内容:里面包含多个步骤
class XiaohongshuUploader:
    COOKIE_PATH = get_file_path("cookie/xiaohongshu_cookie_state.json")
    PUBLISH_URL = (
        "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=image&source=official"
    )

    def __init__(self, image_path_list, title: str = "", content: str = ""):
        self.image_path_list = image_path_list
        self.title = title
        self.content = content
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def launch(self):
        print("开始启动")
        self.playwright = await async_playwright().start()
        print("启动完成")
        self.browser = await self.playwright.chromium.launch(headless=False)

        if os.path.exists(self.COOKIE_PATH):
            print("[√] 加载已保存的登录状态...")
            self.context = await self.browser.new_context(
                storage_state=self.COOKIE_PATH,
                permissions=["geolocation"],
                geolocation={"latitude": 31.2304, "longitude": 121.4737},
            )
        else:
            print("[!] 未检测到登录状态，创建新上下文...")
            self.context = await self.browser.new_context(
                permissions=["geolocation"],
                geolocation={"latitude": 31.2304, "longitude": 121.4737},
            )

        self.page = await self.context.new_page()
        await self.page.goto(self.PUBLISH_URL)

        if not os.path.exists(self.COOKIE_PATH):
            input("请手动登录后按回车继续...")
            await self.context.storage_state(path=self.COOKIE_PATH)
            print("[√] 登录状态已保存")
        await self.wait_seconds(1)

    async def switch_to_image_post(self):
        print("🔀 正在切换到【上传图文】Tab...")

        try:
            await self.page.wait_for_selector(".creator-tab .title", timeout=10000)

            tabs = await self.page.query_selector_all(".creator-tab .title")
            target_tab = None

            for tab in tabs:
                text = (await tab.inner_text()).strip()
                if "上传图文" in text:
                    box = await tab.bounding_box()
                    if box and box["x"] > 0 and box["y"] > 0:
                        target_tab = tab
                        break

            if target_tab:
                await target_tab.click()
                print("[√] 已成功切换到【上传图文】Tab")
            else:
                print("[x] 未找到可点击的【上传图文】Tab")

        except Exception as e:
            print(f"[X] 切换失败: {e}")

    async def upload_images(self, images=None):
        print("📤 正在上传图片...")

        try:
            if images is None:
                images = self.image_path_list

            await self.page.wait_for_selector('input.upload-input[type="file"]', timeout=10000)
            file_input = await self.page.query_selector('input.upload-input[type="file"]')

            if file_input:
                await file_input.set_input_files(images)
                print(f"[√] 已上传 {len(images)} 张图片")
            else:
                print("[x] 未找到图片上传输入框")

        except Exception as e:
            print(f"[X] 图片上传失败: {e}")

    async def fill_title_and_content(self):
        print("📝 正在填写标题和正文...")

        try:
            title_input = await self.page.wait_for_selector(
                'input.d-text[placeholder*="填写标题"]', timeout=10000
            )
            await title_input.fill(self.title)
            print(f"[√] 标题已填写：{self.title}")
        except:
            print("[x] 未找到标题输入框")

        try:
            editor = await self.page.wait_for_selector(
                '.tiptap[contenteditable="true"]', timeout=10000
            )
            await editor.click()
            await editor.type(self.content)
            print(f"[√] 正文已填写：{self.content}")
        except:
            print("[x] 未找到正文编辑器")

    async def submit_post(self):
        await self.wait_seconds(3)
        print("🚀 正在尝试点击发布按钮...")

        try:
            await self.page.wait_for_selector('button:has-text("发布")', timeout=10000)
            publish_button = await self.page.query_selector('button:has-text("发布")')

            if publish_button:
                await publish_button.click()
                print("[√] 发布按钮已点击")
            else:
                print("[!] 未找到发布按钮")
        except Exception as e:
            print(f"[X] 发布失败: {e}")

    async def close(self):
        await self.wait_seconds(4)
        await self.browser.close()
        await self.playwright.stop()

    async def wait_seconds(self, seconds):
        print(f"⏳ 等待 {seconds} 秒...")
        await self.page.wait_for_timeout(seconds * 1000)


async def auto_publish_xiaohongshu(images, title, content):
    xhs = XiaohongshuUploader(images, title, content)
    await xhs.launch()   # 启动浏览器
    await xhs.switch_to_image_post() # 切换到上传图文
    await xhs.upload_images() # 上传图片
    await xhs.fill_title_and_content() # 填写标题和内容
    await xhs.submit_post() # 发布
    await xhs.close() # 关闭浏览器


async def xiaohongshu_auto_publish_node(state: AgentState, config:RunnableConfig):
    """根据用户输入生成中医养生类的小红书文案（包括标题、内容、策略）"""
    print("开始发布小红书")

    print("开始发布小红书")
    title = state["xiaohongshu_tcm_post_title"]
    content = state["xiaohongshu_tcm_post_content"]
    images = state["xiaohongshu_image_path_list"]

    await auto_publish_xiaohongshu(images, title, content)
    state["xiaohongshu_tcm_tip"] = "小红书发布成功！"
    print("完成发布小红书")
    return state


# FastAPI 或脚本运行入口
if __name__ == "__main__":
    asyncio.run(
        auto_publish_xiaohongshu(
            images=[get_file_path("picture/20260608171356南京3日游.png")],
            title="中医养生",
            content="中医养生",
        )
    )
