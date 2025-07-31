import json
import time
from typing import Annotated, ClassVar, Sequence, TypedDict, Optional

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.tools import tool, BaseTool

from app.prompts import decision_making_prompt, planning_prompt, agent_prompt, judge_prompt
from app.utils.format import format_tools_description
from app.config import CORE_API_KEY

# Tool Imports
from app.tools.core_api import CoreAPIWrapper
from app.tools.download import download_and_extract_text
from app.tools.feedback import ask_human_feedback

from langchain_google_genai import ChatGoogleGenerativeAI
from IPython.display import display, Markdown

from app.utils.history import save_entry, get_cached_answer


### SCHEMAS

class SearchPapersInput(BaseModel):
    query: str = Field(description="The query to search for.")
    max_papers: int = Field(default=1, ge=1, le=10)

class DecisionMakingOutput(BaseModel):
    requires_research: bool
    answer: Optional[str] = None

class JudgeOutput(BaseModel):
    is_good_answer: bool
    feedback: Optional[str] = None


### TOOLS
@tool("search-papers", args_schema=SearchPapersInput)
def search_papers(query: str, max_papers: int = 1) -> str:
    """Search scientific papers using the CORE API with a query and number of papers to return."""
    try:
        return CoreAPIWrapper(top_k_results=max_papers).search(query)
    except Exception as e:
        return f"Error performing paper search: {e}"

@tool("download-paper")
def download_paper(url: str) -> str:
    """Download and extract text from a scientific paper PDF using the provided URL."""
    return download_and_extract_text(url)

@tool("ask-human-feedback")
def ask_feedback(question: str) -> str:
    """Ask the user for feedback through terminal input."""
    return ask_human_feedback(question)

tools = [search_papers, download_paper, ask_feedback]
tools_dict = {tool.name: tool for tool in tools}


### LLMS

base_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.0)
decision_making_llm = base_llm.with_structured_output(DecisionMakingOutput)
judge_llm = base_llm.with_structured_output(JudgeOutput)
agent_llm = base_llm.bind_tools(tools)


### STATE

class AgentState(TypedDict):
    requires_research: bool
    is_good_answer: bool
    num_feedback_requests: int
    messages: Annotated[Sequence[BaseMessage], add_messages]


### GRAPH NODES

def decision_making_node(state: AgentState):
    system_prompt = SystemMessage(content=decision_making_prompt)
    response: DecisionMakingOutput = decision_making_llm.invoke([system_prompt] + state["messages"])
    output = {"requires_research": response.requires_research}
    if response.answer:
        output["messages"] = [AIMessage(content=response.answer)]
    return output

def planning_node(state: AgentState):
    system_prompt = SystemMessage(content=planning_prompt.format(tools=format_tools_description(tools)))
    response = base_llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

def tools_node(state: AgentState):
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_result = tools_dict[tool_call["name"]].invoke(tool_call["args"])
        outputs.append(
            ToolMessage(
                content=json.dumps(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}

def agent_node(state: AgentState):
    system_prompt = SystemMessage(content=agent_prompt)
    response = agent_llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

def judge_node(state: AgentState):
    num_feedback_requests = state.get("num_feedback_requests", 0)
    if num_feedback_requests >= 2:
        return {"is_good_answer": True}
    system_prompt = SystemMessage(content=judge_prompt)
    response: JudgeOutput = judge_llm.invoke([system_prompt] + state["messages"])
    output = {
        "is_good_answer": response.is_good_answer,
        "num_feedback_requests": num_feedback_requests + 1
    }
    if response.feedback:
        output["messages"] = [AIMessage(content=response.feedback)]
    return output


### ROUTERS

def router(state: AgentState):
    return "planning" if state["requires_research"] else "end"

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    return "continue" if last_message.tool_calls else "end"

def final_answer_router(state: AgentState):
    return "end" if state["is_good_answer"] else "planning"


### LANGGRAPH WORKFLOW

workflow = StateGraph(AgentState)
workflow.add_node("decision_making", decision_making_node)
workflow.add_node("planning", planning_node)
workflow.add_node("tools", tools_node)
workflow.add_node("agent", agent_node)
workflow.add_node("judge", judge_node)

workflow.set_entry_point("decision_making")

workflow.add_conditional_edges("decision_making", router, {
    "planning": "planning",
    "end": END
})
workflow.add_edge("planning", "agent")
workflow.add_edge("tools", "agent")
workflow.add_conditional_edges("agent", should_continue, {
    "continue": "tools",
    "end": "judge"
})
workflow.add_conditional_edges("judge", final_answer_router, {
    "planning": "planning",
    "end": END
})

app = workflow.compile()


### INTERFACE FUNCTION

# async def print_stream(app: CompiledStateGraph, input: str) -> Optional[BaseMessage]:
#     display(Markdown("## New research running"))
#     display(Markdown(f"### Input:\n\n{input}\n\n"))
#     display(Markdown("### Stream:\n\n"))

#     all_messages = []
#     async for chunk in app.astream({"messages": [input]}, stream_mode="updates"):
#         for updates in chunk.values():
#             if messages := updates.get("messages"):
#                 all_messages.extend(messages)
#                 for message in messages:
#                     message.pretty_print()
#                     print("\n\n")
#     return all_messages[-1] if all_messages else None
async def print_stream(app: CompiledStateGraph, input: str) -> tuple[list[str], Optional[str]]:
    timeline = []
    all_messages = []

    async for chunk in app.astream({"messages": [input]}, stream_mode="updates"):
        for updates in chunk.values():
            if messages := updates.get("messages"):
                all_messages.extend(messages)
                for message in messages:
                    role = message.__class__.__name__
                    content = message.content.strip()
                    if content:
                        timeline.append(f"<b>{role}:</b> {content}")

    #  Filter out self-review messages like "The answer now directly answers..."
    for message in reversed(all_messages):
        if isinstance(message, AIMessage):
            content = message.content.strip()
            if not content.lower().startswith("the answer now directly answers"):
                return timeline, content

    return timeline, "No valid final answer."



# async def run_query(user_input: str) -> str:
#     try:
#         final_response = await print_stream(app, user_input)
#         # return final_response.content if final_response else "No result returned."
#         return final_response.content.strip().split("================================")[0] if final_response else "No result returned."
#     except Exception as e:
#         return f"An error occurred: {e}"
# async def run_query(user_input: str) -> dict:
#     try:
#         steps, final = await print_stream(app, user_input)
#         return {
#             "timeline": steps,
#             "final": final
#         }
#     except Exception as e:
#         return {
#             "timeline": [f"<b>Error:</b> {str(e)}"],
#             "final": "An error occurred."
#         }



async def run_query(user_input: str) -> dict:
    # 1. Check if question is already answered
    cached = get_cached_answer(user_input)
    if cached:
        return cached

    # 2. Run the agent if not cached
    try:
        timeline, final = await print_stream(app, user_input)
        save_entry(user_input, timeline, final)  #  Save result
        return {
            "timeline": timeline,
            "final": final
        }
    except Exception as e:
        return {
            "timeline": [f"<b>Error:</b> {str(e)}"],
            "final": "An error occurred."
        }
