import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agent.tools import query_database, predict_churn, get_churn_risk_list

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

tools = [query_database, predict_churn, get_churn_risk_list]

llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    anthropic_api_key=ANTHROPIC_API_KEY,
    temperature=0
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are SalesIQ, an intelligent sales assistant for a B2B software company.
You help sales teams understand their customers, identify risks, and make data-driven decisions.

You have access to these tools:
1. query_database - Query the sales database for any information
2. predict_churn - Predict if a specific customer is at risk of leaving
3. get_churn_risk_list - Get a ranked list of customers most at risk

Guidelines:
- Always be helpful, concise and professional
- When asked about revenue, customers, or data use query_database
- When asked about a specific customer churn risk use predict_churn
- When asked for a list of at-risk customers use get_churn_risk_list
- Format numbers nicely
- If you don't know something, say so honestly
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    k=10
)

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True
)


def chat(message: str) -> str:
    try:
        response = agent_executor.invoke({"input": message})
        output = response["output"]
        # Handle case where output is a list of dicts
        if isinstance(output, list):
            for item in output:
                if isinstance(item, dict) and "text" in item:
                    return item["text"]
        return str(output)
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"


if __name__ == "__main__":
    print("SalesIQ Agent ready! Type your questions below.")
    print("Type 'quit' to exit\n")
    print("-" * 50)

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        if not user_input:
            continue

        print("\nSalesIQ thinking...")
        response = chat(user_input)
        print(f"\nSalesIQ: {response}")
        print("-" * 50)