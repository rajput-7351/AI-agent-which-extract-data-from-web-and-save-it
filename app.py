import streamlit as st
import uuid
from agent import create_agent, run_agent, get_final_answer

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchAgent",
    page_icon="🤖",
    layout="wide",
)

# ── Session state ─────────────────────────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "agent_loaded" not in st.session_state:
    st.session_state.agent_loaded = False


# ── Load agent ────────────────────────────────────────────────────────────────
@st.cache_resource
def load_agent():
    return create_agent()


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🤖 ResearchAgent")
st.caption("An AI agent that searches the web, reads pages, runs code, and saves results.")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Agent Controls")

    if st.button("🚀 Initialize Agent", use_container_width=True, type="primary"):
        with st.spinner("Loading agent..."):
            try:
                st.session_state.agent = load_agent()
                st.session_state.agent_loaded = True
                st.success("Agent ready!")
            except Exception as e:
                st.error(f"Failed to load agent: {e}")

    st.divider()

    if st.button("🗑️ New Conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.success("Started new conversation!")
        st.rerun()

    st.divider()

    # Example tasks
    st.markdown("#### 💡 Example tasks")
    examples = [
        "Search for the latest news about artificial intelligence",
        "What is LangGraph and how does it work?",
        "Calculate the compound interest on $10000 at 8% for 5 years",
        "Research Python best practices and save a summary to best_practices.txt",
        "Scrape https://python.org and summarize what you find",
    ]
    for example in examples:
        if st.button(example, use_container_width=True):
            st.session_state["prefill"] = example
            st.rerun()

    st.divider()

    # Tools info
    st.markdown("#### 🛠️ Available tools")
    st.markdown("""
    - 🔍 **Web search** — DuckDuckGo
    - 🌐 **Website scraper** — BeautifulSoup
    - 💾 **File saver** — saves to agent_outputs/
    - 🐍 **Python REPL** — runs calculations
    """)

    st.divider()
    st.caption(f"Session ID: `{st.session_state.thread_id[:8]}...`")


# ── Main chat area ────────────────────────────────────────────────────────────
if not st.session_state.agent_loaded:
    st.info("👈 Click **Initialize Agent** in the sidebar to get started.")
    st.stop()

# Render chat history
for message in st.session_state.chat_history:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(message["content"])
            # Show agent steps in expander
            if "steps" in message and message["steps"]:
                with st.expander("🔍 Agent reasoning steps"):
                    for step in message["steps"]:
                        if step["type"] == "tool_call":
                            st.markdown(f"**Using tool:** `{step['tool']}`")
                            with st.expander(f"Input to {step['tool']}"):
                                st.json(step["input"])
                        elif step["type"] == "tool_result":
                            with st.expander(f"Result from `{step['tool']}`"):
                                st.text(str(step["output"])[:1000])
                        elif step["type"] == "error":
                            st.error(step["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", "")
user_input = st.chat_input(
    "Ask the agent to research, calculate, or save anything...",
)

# Handle either typed input or sidebar example click
query = user_input or prefill

if query:
    # Show user message
    st.session_state.chat_history.append({
        "role": "user",
        "content": query,
    })
    with st.chat_message("user"):
        st.markdown(query)

    # Run agent
    with st.chat_message("assistant"):
        # Live step display
        step_placeholder = st.empty()
        status_messages = []

        with st.spinner("Agent is thinking..."):
            steps = run_agent(
                st.session_state.agent,
                query,
                st.session_state.thread_id,
            )

        # Show live reasoning steps
        tool_calls_made = [s for s in steps if s["type"] == "tool_call"]
        if tool_calls_made:
            tools_used = [s["tool"] for s in tool_calls_made]
            step_placeholder.info(
                f"Used tools: {', '.join(set(tools_used))}"
            )

        # Final answer
        answer = get_final_answer(steps)
        st.markdown(answer)

        # Reasoning expander
        if steps:
            with st.expander("🔍 Agent reasoning steps"):
                for step in steps:
                    if step["type"] == "tool_call":
                        st.markdown(f"**Using tool:** `{step['tool']}`")
                        with st.expander(f"Input to {step['tool']}"):
                            st.json(step["input"])
                    elif step["type"] == "tool_result":
                        with st.expander(f"Result from `{step['tool']}`"):
                            st.text(str(step["output"])[:1000])
                    elif step["type"] == "error":
                        st.error(step["content"])

    # Save to history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer,
        "steps": steps,
    })