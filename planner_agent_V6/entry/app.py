import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
API_URL = f"{API_BASE}/chat"
CONFIGURE_URL = f"{API_BASE}/configure"
HEALTH_URL = f"{API_BASE}/health"

st.set_page_config(page_title="Planner Agent", layout="centered")

# ── 会话状态初始化 ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "configured" not in st.session_state:
    # 页面首次加载时，探测后端是否已有 Agent（支持刷新后自动恢复）
    try:
        resp = requests.get(HEALTH_URL, timeout=3)
        st.session_state.configured = resp.json().get("configured", False)
    except Exception:
        st.session_state.configured = False

st.title("🤖 Planner Agent Demo")

# ═══════════════════════════════════════════════════════════════
#  侧边栏: API 配置
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("🔑 API 配置")

    if st.session_state.configured:
        st.success("✅ 已连接")
        if st.button("断开连接"):
            st.session_state.configured = False
            st.rerun()
    else:
        st.info("请输入 API Key 后点击保存")

    st.divider()

    deepseek_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        placeholder="sk-...",
        help="在 https://platform.deepseek.com 注册获取",
    )

    tavily_key = st.text_input(
        "Tavily API Key (可选)",
        type="password",
        placeholder="tvly-...",
        help="网络搜索工具需要，不填则 web_search 不可用",
    )

    if st.button("保存并连接", type="primary", use_container_width=True):
        if not deepseek_key.strip():
            st.error("DeepSeek API Key 不能为空")
        else:
            with st.spinner("正在连接..."):
                try:
                    resp = requests.post(
                        CONFIGURE_URL,
                        json={
                            "deepseek_key": deepseek_key.strip(),
                            "tavily_key": tavily_key.strip(),
                        },
                        timeout=10,
                    )
                    if resp.ok:
                        st.session_state.configured = True
                        st.success("已连接！可以开始对话")
                        st.rerun()
                    else:
                        detail = resp.json().get("detail", resp.text)
                        st.error(f"连接失败: {detail}")
                except requests.ConnectionError:
                    st.error("无法连接到后端，请确认 API 服务已启动")
                except Exception as e:
                    st.error(f"连接失败: {e}")

    st.divider()

    # ── 控制面板 ──
    st.header("控制面板")

    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()

    st.write(f"当前消息数：{len(st.session_state.messages)}")

# ═══════════════════════════════════════════════════════════════
#  展示历史消息
# ═══════════════════════════════════════════════════════════════
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ═══════════════════════════════════════════════════════════════
#  输入框
# ═══════════════════════════════════════════════════════════════
if not st.session_state.configured:
    st.info("👈 请先在侧边栏配置 API Key，然后即可开始对话")
    st.stop()

question = st.chat_input("请输入问题...")

if question:
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.write(question)

    # AI 回复
    with st.chat_message("assistant"):
        with st.spinner("Agent 思考中..."):
            try:
                response = requests.post(
                    API_URL,
                    json={"query": question},
                    timeout=120,
                )

                if response.status_code == 400:
                    detail = response.json().get("detail", "")
                    if "配置" in detail or "configure" in detail.lower():
                        answer = "请先在侧边栏配置 API Key"
                        st.session_state.configured = False
                    else:
                        answer = f"请求失败：{detail}"
                else:
                    result = response.json()
                    answer = result["answer"]

            except requests.ConnectionError:
                answer = "请求失败：无法连接到后端服务"
            except Exception as e:
                answer = f"请求失败：{str(e)}"

        st.write(answer)

    # 保存 AI 消息
    st.session_state.messages.append({"role": "assistant", "content": answer})
