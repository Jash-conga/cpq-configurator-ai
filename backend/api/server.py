"""
backend/api/server.py

FastAPI server (future wiring).
Currently a placeholder that wires the CPQAgent to HTTP endpoints.

Start with:
    uvicorn backend.api.server:app --reload --port 8000

Endpoints:
    POST /chat       — Send a message to the agent
    GET  /state      — Get current running JSON
    POST /reset      — Clear conversation and running JSON
    POST /deploy     — Trigger Salesforce deployment
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.cpq_agent import CPQAgent
from state.running_json import get_state, clear_state
from utils.logger import get_logger

logger = get_logger("api_server")

app = FastAPI(title="Conga CPQ AI Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single agent instance per server process
_agent = CPQAgent()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    running_json: dict


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info("api_chat_request", message_preview=request.message[:80])
    response_text = _agent.chat(request.message)
    return ChatResponse(response=response_text, running_json=get_state())


@app.get("/state")
async def get_running_state():
    return get_state()


@app.post("/reset")
async def reset():
    _agent.reset()
    clear_state()
    logger.info("api_session_reset")
    return {"status": "reset"}


@app.post("/deploy")
async def deploy():
    from backend.salesforce.sf_client import deploy_running_json
    result = deploy_running_json()
    return result
