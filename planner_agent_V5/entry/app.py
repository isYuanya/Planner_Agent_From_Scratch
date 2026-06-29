import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(page_title="Planner Agent", layout="centered")

# 初始化
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🤖 Planner Agent Demo")

# 侧边栏
with st.sidebar:
    st.header("控制面板")

    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()

    st.write(f"当前消息数：{len(st.session_state.messages)}")

# 展示历史消息（Chat风格）
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 输入框（ChatGPT风格）
question = st.chat_input("请输入问题...")

if question:

    # 显示用户消息
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.write(question)

    # AI回复占位 + loading
    with st.chat_message("assistant"):
        with st.spinner("Agent思考中..."):

            try:
                response = requests.post(
                    API_URL,
                    json={"query": question},
                    timeout=60
                )

                result = response.json()
                answer = result["answer"]

            except Exception as e:
                answer = f"请求失败：{str(e)}"

        st.write(answer)

    # 保存AI消息
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })