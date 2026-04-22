import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent.agent import chat

app = FastAPI(
    title="SalesIQ API",
    description="AI-powered sales intelligence chatbot API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    status: str = "success"


@app.get("/")
def root():
    return {"status": "SalesIQ API is running"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint.
    Send a message, get a response from the AI agent.
    """
    response = chat(request.message)
    return ChatResponse(response=response)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "SalesIQ"}