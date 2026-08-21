# app.py
import json
import time

import streamlit as st
import requests

# 后端接口
BACKEND_URL = "http://127.0.0.1:8000/process"


def get_user_id():
    return 'user_001'


def query_zhongyi_fastapi(input: str):
    """按行消费流式响应，每行一个 JSON。"""
    payload = {"input": input, "user_id": get_user_id()}
    response = requests.post(BACKEND_URL, json=payload, stream=True, timeout=60)
    if response.status_code != 200:
        yield {"type": "done", "msg": f"请求错误: {response.status_code}"}
        return
    buffer = ""
    for chunk in response.iter_content(chunk_size=1024):
        if not chunk:
            continue
        buffer += chunk.decode("utf-8", errors="replace")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue
    if buffer.strip():
        try:
            yield json.loads(buffer.strip())
        except json.JSONDecodeError:
            pass


# 页面设置
st.set_page_config(page_title="中医对话机器人", page_icon="💬", layout="centered")
st.title("💬 中医对话机器人")
st.write("和智能机器人进行对话")

# 初始化聊天记录，session_state, 字典，存储聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []


def _stream_display(placeholder, text: str, step: int = 2, delay: float = 0.03):
    """在前端模拟流式输出：逐段更新占位符。"""
    for i in range(step, len(text) + 1, step):
        placeholder.markdown(text[:i])
        time.sleep(delay)
    placeholder.markdown(text)


def _hide_thinking_show_process(thinking_container, think_placeholder_content: str):
    """隐藏「正在思考...」，改为折叠的「思考过程」（有内容才显示）。"""
    thinking_container.empty()
    with thinking_container:
        if (think_placeholder_content or "").strip():
            with st.expander("思考过程", expanded=False):
                st.text(think_placeholder_content)


def run_process(input: str, think_placeholder, reply_placeholder, thinking_container):
    think_placeholder_content = "" # 思考过程内容
    reply_placeholder_content = "" # 回复内容
    thinking_hidden = False  # 是否已隐藏「正在思考」

    for chunk_dict in query_zhongyi_fastapi(input):
        # 回复内容是实时显示在页面上的(yield)
        if not isinstance(chunk_dict, dict):
            continue
        if chunk_dict.get("type") == "msg":  #思考->内容
            content = chunk_dict.get("msg") or ""
            think_placeholder_content += content
            if not thinking_hidden:
                think_placeholder.text(think_placeholder_content) #显示思考过程
        elif chunk_dict.get("type") == "reply": # 回复->内容
            content = chunk_dict.get("msg") or ""
            reply_placeholder_content += content
            reply_placeholder.markdown(reply_placeholder_content)
            # 一旦有回复内容就立刻隐藏「正在思考...」
            if not thinking_hidden:
                thinking_hidden = True
                _hide_thinking_show_process(thinking_container, think_placeholder_content)
        elif chunk_dict.get("type") == "done": # 结束
            done_msg = (chunk_dict.get("msg") or "").strip()
            if not reply_placeholder_content.strip() and done_msg:
                _stream_display(reply_placeholder, done_msg)
                reply_placeholder_content = done_msg
            else:
                reply_placeholder.markdown(reply_placeholder_content or done_msg)
            st.session_state.messages.append(
                {"role": "assistant",
                 "content": reply_placeholder_content or done_msg or "（暂无回复内容）",
                 "think_content": think_placeholder_content})
            # 用历史记录重绘页面，已完成的回复只显示「思考过程」+ 内容，「正在思考」不再出现
            st.rerun()


# 显示已有的聊天记录
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    else:
        with st.chat_message(message["role"]):
            # 已有回复结果时只显示「思考过程」折叠框（有内容才显示），不再显示「正在思考...」
            if message.get("think_content", "").strip():
                with st.expander("思考过程", expanded=False):
                    st.text(message["think_content"])
            st.markdown(message["content"])

# 输入框（Streamlit 的聊天输入组件）
if prompt := st.chat_input("请输入您的问题..."):
    # 如果用户进行输入，才进入这个代码
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

    # 显示模型的回复（思考区用 container，便于收到结果后替换为「思考过程」）
    with st.chat_message("assistant"):
        thinking_container = st.container()
        with thinking_container:
            st.caption("正在思考...")
            think_placeholder = st.empty()
        reply_placeholder = st.empty()

    run_process(prompt, think_placeholder, reply_placeholder, thinking_container)
