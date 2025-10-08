from typing import Literal, AsyncGenerator
from langgraph.graph import StateGraph, END, MessagesState
from langchain_core.messages import AIMessage, HumanMessage
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

# --- 1. Load API Keys and Initialize LLM ---
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, streaming=True)

# --- 2. Define the State ---
class SupervisorState(MessagesState):
    next_agent: str
    current_task: str
    explanation: str
    doubt_answer: str
    learning_path: str

# --- 3. Define the Agent Nodes ---

def supervisor_agent(state: SupervisorState) -> dict:
    task = state["messages"][-1].content
    supervisor_prompt = f"""
    You are a supervisor managing a team of AI agents for a learning assistant.
    Greet the user in the starting when he comes or says words like "Hello", "Hello Assistant".
    Greet him back with warm words".
    Based on the user's last message, decide which agent should work next or if the task is complete.

    Your agents are:
    - explainer: Explains a topic in detail.
    - solver: Solves a specific doubt or answers a follow-up question.
    - coach: Creates a personalized learning path.

    User's Request: "{task}"

    Respond with ONLY the agent's name (explainer, solver, coach) or "END" if the request is a simple closing statement like "thanks".
    """
    response = llm.invoke(supervisor_prompt)
    decision = response.content.strip().lower()
    print(f"--- Supervisor Decision: {decision} ---")
    return {"next_agent": decision, "current_task": task}

async def content_explainer_agent(state: SupervisorState) -> AsyncGenerator[dict, None]:
    task = state["current_task"]
    print(f"--- Explainer Agent: Explaining '{task}' ---")
    prompt = f"Provide a detailed explanation of the topic: {task}"
    collected_content = ""
    async for chunk in llm.astream(prompt):
        if chunk.content:
            collected_content += chunk.content
            yield {
                "messages": [AIMessage(content=collected_content)],
                "explanation": collected_content
            }

async def doubt_solving_agent(state: SupervisorState) -> AsyncGenerator[dict, None]:
    doubt = state["current_task"]
    context = state.get("explanation", "No prior context available.")
    print(f"--- Doubt Solver Agent: Solving '{doubt}' ---")
    prompt = f"A user has the following doubt: '{doubt}'. Based on the prior context ('{context}'), provide a clear and direct answer."
    collected_content = ""
    async for chunk in llm.astream(prompt):
        if chunk.content:
            collected_content += chunk.content
            yield {
                "messages": [AIMessage(content=collected_content)],
                "doubt_answer": collected_content
            }

async def personalized_learning_agent(state: SupervisorState) -> AsyncGenerator[dict, None]:
    goal = state["current_task"]
    print(f"--- Learning Coach Agent: Creating path for '{goal}' ---")
    prompt = f"Create a personalized, step-by-step learning path for a user whose goal is: '{goal}'. Include key topics and suggested resources."
    collected_content = ""
    async for chunk in llm.astream(prompt):
        if chunk.content:
            collected_content += chunk.content
            yield {
                "messages": [AIMessage(content=collected_content)],
                "learning_path": collected_content
            }

# --- 4. Define the Router ---
def router(state: SupervisorState) -> Literal["explainer", "solver", "coach", "__end__"]:
    decision = state.get("next_agent", "").strip()
    if "explainer" in decision:
        return "explainer"
    elif "solver" in decision:
        return "solver"
    elif "coach" in decision:
        return "coach"
    else:
        return "__end__"

# --- 5. Build and Compile the Graph ---
workflow = StateGraph(SupervisorState)
workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("explainer", content_explainer_agent)
workflow.add_node("solver", doubt_solving_agent)
workflow.add_node("coach", personalized_learning_agent)
workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    router,
    {
        "explainer": "explainer",
        "solver": "solver",
        "coach": "coach",
        "__end__": END
    }
)
workflow.add_edge("explainer", END)
workflow.add_edge("solver", END)
workflow.add_edge("coach", END)
agent_graph = workflow.compile()

