"""
AI Service - Financial AI Copilot
Conversational AI that understands personal finance context via RAG + LLM
"""
from typing import List, Optional, AsyncGenerator
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import openai
import json

from app.core.config import settings
from app.services.rag_service import RAGService
from app.services.context_builder import FinancialContextBuilder
from app.core.redis_client import redis_client

router = APIRouter()


# ── Schemas ─────────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class CopilotRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    stream: bool = True
    user_id: Optional[str] = None


class CopilotResponse(BaseModel):
    conversation_id: str
    response: str
    sources: List[dict] = []
    financial_context_used: bool = False
    tokens_used: int = 0
    created_at: datetime


# ── System Prompt ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are **FinanceIQ**, an elite AI financial copilot for ExpenseFlow X.

You help users make smarter financial decisions by:
- Analyzing their personal spending patterns and financial data
- Answering questions about their budget, expenses, savings, and investments
- Providing actionable, personalized financial advice
- Detecting risks and opportunities in their financial life
- Explaining complex financial concepts in simple terms

🌍 Context: You operate in the Indian financial ecosystem (₹/INR, GST, SIPs, PPF, EPF, etc.)

📊 When financial data is provided in the context, always:
1. Reference specific numbers from their actual data
2. Give concrete, actionable recommendations
3. Show calculations when relevant
4. Be empathetic and encouraging

⚠️ Always remind users you are an AI and not a licensed financial advisor for major decisions.

Format your responses with:
- Clear headers using **bold**
- Bullet points for lists
- Numbers/₹ symbols for amounts
- Emojis for better readability 📈💰
"""


# ── Routes ───────────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(payload: CopilotRequest):
    """Chat with the AI Financial Copilot (streaming supported)"""
    conversation_id = payload.conversation_id or str(uuid.uuid4())

    # Load conversation history from Redis
    history_key = f"copilot:history:{conversation_id}"
    history_raw = await redis_client.get(history_key)
    conversation_history: List[dict] = json.loads(history_raw) if history_raw else []

    # Build financial context for RAG
    financial_context = ""
    if payload.user_id:
        try:
            context_builder = FinancialContextBuilder(payload.user_id)
            financial_context = await context_builder.build_context(payload.message)
        except Exception:
            pass  # Continue without context if unavailable

    # Retrieve relevant knowledge from RAG
    rag_context = ""
    try:
        rag_service = RAGService()
        rag_results = await rag_service.search(payload.message, top_k=3)
        if rag_results:
            rag_context = "\n\n📚 **Relevant Financial Knowledge:**\n" + "\n".join(
                f"- {r['content']}" for r in rag_results
            )
    except Exception:
        pass

    # Build messages
    system_content = SYSTEM_PROMPT
    if financial_context:
        system_content += f"\n\n📊 **User's Financial Context:**\n{financial_context}"
    if rag_context:
        system_content += rag_context

    messages = [
        {"role": "system", "content": system_content},
        *conversation_history[-20:],  # Keep last 20 messages for context window
        {"role": "user", "content": payload.message},
    ]

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    if payload.stream:
        async def stream_response() -> AsyncGenerator[str, None]:
            full_response = ""
            try:
                stream = await client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=1500,
                )
                async for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        full_response += delta
                        yield f"data: {json.dumps({'content': delta, 'conversation_id': conversation_id})}\n\n"

                # Save to history
                conversation_history.extend([
                    {"role": "user", "content": payload.message},
                    {"role": "assistant", "content": full_response},
                ])
                await redis_client.setex(history_key, 86400, json.dumps(conversation_history))
                yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(stream_response(), media_type="text/event-stream")

    else:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
        )
        assistant_message = response.choices[0].message.content

        conversation_history.extend([
            {"role": "user", "content": payload.message},
            {"role": "assistant", "content": assistant_message},
        ])
        await redis_client.setex(history_key, 86400, json.dumps(conversation_history))

        return CopilotResponse(
            conversation_id=conversation_id,
            response=assistant_message,
            financial_context_used=bool(financial_context),
            tokens_used=response.usage.total_tokens,
            created_at=datetime.utcnow(),
        )


@router.delete("/chat/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    await redis_client.delete(f"copilot:history:{conversation_id}")
    return {"message": "Conversation cleared", "conversation_id": conversation_id}


@router.get("/chat/{conversation_id}/history")
async def get_history(conversation_id: str):
    """Get conversation history"""
    history_raw = await redis_client.get(f"copilot:history:{conversation_id}")
    history = json.loads(history_raw) if history_raw else []
    return {"conversation_id": conversation_id, "messages": history}
