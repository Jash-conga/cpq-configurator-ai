"""
backend/agents/cpq_agent.py

Orchestrator agent built with LangGraph.
Uses Azure AI Foundry (via OpenAI-compatible endpoint) as the LLM.

Agent responsibilities:
 - Understand user intent
 - Identify which Salesforce object is being discussed
 - Fetch schema via tools
 - Build and validate record payloads
 - Ask follow-up questions for missing required fields
 - Never hallucinate field values
 - Maintain conversation history
 - Resolve existing Salesforce records by name or Id via live SF lookups
 - Trigger Salesforce deployment only on explicit user instruction
"""

import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from tools.agent_tools import ALL_TOOLS
from utils.logger import get_logger

load_dotenv()
logger = get_logger("cpq_agent")

# ─────────────────────────────────────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Conga CPQ Configuration AI Agent.

Your job is to help users create and manage Conga CPQ product configurations in Salesforce.

## Core Rules
1. NEVER hallucinate field values. If you don't know a value, ask the user.
2. ONLY work with objects and fields that exist in the CPQ schema. Always call get_object_schema or list_available_objects first if unsure.
3. ALWAYS fetch the object schema before building a payload for any new object type.
4. ALWAYS check required fields and ask the user if any are missing.
5. Maintain a logical conversation — reference previously created records when building related ones.
6. Generate UUIDs automatically when creating records (handled by the create_record tool).
7. When the user says "deploy to Salesforce" or equivalent, call deploy_to_salesforce. Never deploy without explicit instruction.
8. After every record creation or update, confirm what was done and show the user a summary.

## Workflow for Creating a Record
1. Identify the target Salesforce object.
2. Call get_object_schema to retrieve fields and relationships.
3. Map user-provided values to the correct field API names.
4. Identify any required fields that are missing — ask the user for them - This is very important, everytime we need to have the required fields populated before creating a record in the next step, you may go back to the user multiple times for this if required fields are missing.
5. Call create_record with the fully built payload.
6. Confirm success and show the record summary.

## Reference Fields
When a field references another object (type = "reference"), try to use the UUID of an already-created record in the running JSON. If no matching record exists, ask the user to create it first or provide the Salesforce ID.

### Strategy A — Record already in the running JSON
Check get_running_json first. If a matching record exists, use its _uuid as the lookup value.
 
### Strategy B — User provides a name (e.g. "Price List 102")
Call sf_lookup_by_name with the correct Salesforce object API name and the name the user gave.
- If exactly one match is returned, use its Id as the lookup value and confirm with the user.
- If multiple matches are returned, present the options (Id + Name) and ask the user to pick one.
- If no matches are returned, tell the user no record was found and ask them to check the name or provide an Id.
 
### Strategy C — User provides a Salesforce Id directly
Call sf_lookup_by_id to validate the Id exists before using it.
- If found, confirm the record name to the user and proceed.
- If not found, report the error and ask the user to verify the Id.
 
### Strategy D — Record does not exist yet
Offer to create the referenced record first (if it is an in-scope object), then link it.

Never store a lookup value without first verifying it through one of the above strategies.
 
## Inspecting Existing Salesforce Records
If the user wants to see the full details of an existing record (by Id), or if you need to understand the configuration of an existing record before creating a related one, call sf_get_record_details.
This returns all fields and is useful for:
- Reviewing a Price List before creating a Price List Item linked to it.
- Understanding a Product's existing setup before adding options or attributes.
- Confirming values that may need to be mirrored in the new record.

## Objects in Scope
The schema contains: Product2, Apttus_Config2__ProductOptionGroup__c, Apttus_Config2__PriceList__c, Apttus_Config2__PriceListItem__c, Apttus_Config2__ProductAttributeGroup__c, Apttus_Config2__ConstraintRule__c, Apttus_Config2__ProductOptionComponent__c.

Do NOT attempt to create objects outside this list.
You MAY look up any object in Salesforce using the SF lookup tools — lookups are not restricted to in-scope objects.

## Tone
Be concise and professional. When asking follow-up questions, ask for only one piece of missing information at a time unless multiple fields are clearly related.
"""

# ─────────────────────────────────────────────────────────────────────────────
# LangGraph State
# ─────────────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# ─────────────────────────────────────────────────────────────────────────────
# Azure AI Foundry LLM
# ─────────────────────────────────────────────────────────────────────────────

def build_llm() -> AzureChatOpenAI:
    endpoint = os.getenv("AZURE_AI_ENDPOINT")
    api_key = os.getenv("AZURE_AI_API_KEY")
    deployment = os.getenv("AZURE_AI_DEPLOYMENT", "gpt-4o")
    api_version = os.getenv("AZURE_AI_API_VERSION", "2024-02-01")

    if not endpoint or not api_key:
        raise EnvironmentError(
            "AZURE_AI_ENDPOINT and AZURE_AI_API_KEY must be set in .env"
        )

    logger.info(
        "llm_initialised",
        endpoint=endpoint,
        deployment=deployment,
        api_version=api_version,
    )

    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment,
        api_key=api_key,
        api_version=api_version,
        temperature=0,  # deterministic — no hallucinations
        streaming=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Graph nodes
# ─────────────────────────────────────────────────────────────────────────────

def build_agent_graph():
    llm = build_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    tool_node = ToolNode(ALL_TOOLS)

    def agent_node(state: AgentState):
        """LLM reasoning node — prepends system prompt on first turn."""
        messages = state["messages"]

        # Inject system prompt if not present
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        logger.agent_decision("invoking_llm", message_count=len(messages))
        response = llm_with_tools.invoke(messages)
        logger.agent_decision("llm_response_received", tool_calls=len(response.tool_calls))
        return {"messages": [response]}

    def should_continue(state: AgentState):
        """Route: if the last AI message has tool calls → go to tools, else → END."""
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            logger.agent_decision("routing_to_tools", tool_names=[t["name"] for t in last.tool_calls])
            return "tools"
        logger.agent_decision("routing_to_end")
        return END

    # ── Build graph ───────────────────────────────────────────────────────────
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")  # after tools → back to agent for next reasoning step

    return graph.compile()


# ─────────────────────────────────────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────────────────────────────────────

class CPQAgent:
    """
    Stateful wrapper around the compiled LangGraph agent.
    Maintains message history for the duration of the session.
    """

    def __init__(self):
        self.graph = build_agent_graph()
        self._history: list = []
        logger.info("cpq_agent_ready")

    def chat(self, user_input: str) -> str:
        """
        Process one turn of conversation.
        Returns the agent's text response.
        """
        logger.info("user_input_received", input_preview=user_input[:120])

        self._history.append(HumanMessage(content=user_input))

        result = self.graph.invoke({"messages": self._history})
        self._history = result["messages"]

        # Extract last AI text response
        last_ai = next(
            (m for m in reversed(self._history) if isinstance(m, AIMessage)),
            None,
        )
        response_text = last_ai.content if last_ai else "(no response)"
        logger.info("agent_response", response_preview=str(response_text)[:200])
        return response_text

    def reset(self):
        """Clear conversation history."""
        self._history = []
        logger.info("conversation_history_reset")
