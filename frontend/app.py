import streamlit as st
import httpx
import json

# Page configuration
st.set_page_config(
    page_title="SalesIQ - AI Sales Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stChatMessage {
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">SalesIQ</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Sales Intelligence Assistant</div>',
            unsafe_allow_html=True)

# Sidebar with example questions
with st.sidebar:
    st.header("Example Questions")
    st.markdown("Click any question to ask it:")

    example_questions = [
        "How many customers do we have?",
        "What is our total monthly revenue?",
        "Which customers are most at risk of churning?",
        "Show me customers by plan type",
        "What is our revenue by industry?",
        "How many open support tickets do we have?",
        "Show me enterprise customers",
        "What are the top 5 customers by spend?",
    ]

    for question in example_questions:
        if st.button(question, use_container_width=True):
            st.session_state.clicked_question = question

    st.markdown("---")
    st.markdown("**Powered by:**")
    st.markdown("- Claude AI (Anthropic)")
    st.markdown("- LangChain Agent")
    st.markdown("- scikit-learn ML Model")
    st.markdown("- SQLite Database")

    if st.button("Clear Chat", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Welcome message
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant"):
        st.markdown("""
        Hello! I'm **SalesIQ**, your AI sales intelligence assistant.

        I can help you with:
        - 📊 **Database queries** — revenue, customers, transactions
        - 🔮 **Churn prediction** — identify at-risk customers
        - 📋 **Business insights** — trends and patterns

        Try asking me something from the sidebar, or type your own question below!
        """)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle clicked question from sidebar
if "clicked_question" in st.session_state and st.session_state.clicked_question:
    question = st.session_state.clicked_question
    st.session_state.clicked_question = None

    # Add to chat
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    # Get response from API
    with st.chat_message("assistant"):
        with st.spinner("SalesIQ is thinking..."):
            try:
                response = httpx.post(
                    "http://127.0.0.1:8000/chat",
                    json={"message": question},
                    timeout=60.0
                )
                data = response.json()
                answer = data["response"]
            except Exception as e:
                answer = f"Error connecting to API: {str(e)}. Make sure the API server is running."

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    st.rerun()

# Chat input at the bottom
if prompt := st.chat_input("Ask me anything about your sales data..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from API
    with st.chat_message("assistant"):
        with st.spinner("SalesIQ is thinking..."):
            try:
                response = httpx.post(
                    "http://127.0.0.1:8000/chat",
                    json={"message": prompt},
                    timeout=60.0
                )
                data = response.json()
                answer = data["response"]
            except Exception as e:
                answer = f"Error connecting to API: {str(e)}. Make sure the API server is running."

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})