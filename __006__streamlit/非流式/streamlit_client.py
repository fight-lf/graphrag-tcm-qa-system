# app.py
import streamlit as st
import requests

# 后端接口
BACKEND_URL = "http://127.0.0.1:8000/process"

# 前端页面, 调用后端接口
def query_zhongyi_fastapi(input: str) -> str:
    payload = {"input": input}
    res = requests.post(BACKEND_URL, json=payload)
    output = res.json().get("output", (False, "后端没有结果")) # 获取大模型接口返回的结果
    return output


# 页面设置
st.set_page_config(page_title="中医对话机器人", page_icon="💬", layout="centered")
st.title("💬 中医对话机器人")
st.write("和智能机器人进行对话")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 展示历史消息
for msg in st.session_state.messages:
    if msg["role"] == "user": # 用户角色
        st.chat_message("user").write(msg["content"])
    else: # 机器人角色:assistant
        st.chat_message("assistant").markdown(msg["content"], unsafe_allow_html=True)

# 输入框
if prompt := st.chat_input("请输入您的问题..."):
    # 显示用户消息
    with st.chat_message("user"):
        st.write(prompt) # 页面显示用户输入
        # 并添加到历史消息列表中
        st.session_state.messages.append({"role": "user", "content": prompt})

    # 调用后端接口
    response = query_zhongyi_fastapi(prompt)
    with st.chat_message("assistant"):
        st.markdown(response, unsafe_allow_html=True) # 显示机器人的回复
        st.session_state.messages.append({"role": "assistant", "content": response}) # 添加到历史消息列表中
