
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
import re

from app.database.postgre import get_db
from app.models.knowledge import KnowledgeBase
from app.core.config import get_settings
from app.core.rate_limit import limiter

router = APIRouter()
settings = get_settings()



embedding_model = None

def load_model():
    global embedding_model
    if embedding_model is None:
        try:
            print("Đang tải Chat Embedding Model...")
            embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("Chat Embedding Model Ready!")
        except Exception as e:
            print(f"Lỗi tải model embedding: {e}")
            embedding_model = None
    return embedding_model

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

def get_embedding(text: str):
    model = load_model()
    if not model:
        raise HTTPException(status_code=500, detail="Embedding model chưa sẵn sàng.")
    return model.encode(text).tolist()

async def retrieve_knowledge(db: AsyncSession, query_embedding: list, top_k: int = 3, query_text: str = ""):
    try:
        article_match = re.search(r'điều\s+(\d+)', query_text.lower())
        if article_match:
            article_num = article_match.group(1)
            target_id = f"Điều_{article_num}"
            
            stmt = select(KnowledgeBase).where(KnowledgeBase.chunk_id == target_id)
            result = await db.execute(stmt)
            exact_doc = result.scalars().first()
            
            if exact_doc:
                return [exact_doc]
        
        stmt = select(KnowledgeBase).order_by(
            KnowledgeBase.embedding.l2_distance(query_embedding)
        ).limit(top_k)
        
        result = await db.execute(stmt)
        return result.scalars().all()
        
    except Exception as e:
        print(f"Lỗi truy vấn DB: {e}")
        return []

@router.post("/", response_description="Stream NDJSON")
@limiter.limit("5/minute")
async def chat_with_stream(request: Request, body: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Trả về StreamingResponse (NDJSON).
    Line 1: {"type": "sources", "data": [...]}
    Line 2+: {"type": "content", "data": "chunk..."}
    """
    user_msg = body.message
    if not user_msg:
        raise HTTPException(status_code=400, detail="Tin nhắn không được để trống")

    # 1. Retrieve Docs (Fast)
    try:
        query_vec = get_embedding(user_msg)
        relevant_docs = await retrieve_knowledge(db, query_vec, top_k=5, query_text=user_msg)
    except Exception as e:
         print(f"RAG Error: {e}")
         relevant_docs = []

    context_text = ""
    sources = []
    
    for doc in relevant_docs:
        context_text += f"{doc.content}\nSource: {doc.chunk_id}\n\n"
        if doc.chunk_id not in sources:
            sources.append(doc.chunk_id)

    if not context_text:
        context_text = "Không tìm thấy thông tin cụ thể trong bộ luật đang lưu trữ."

    # 2. Build Prompt
    system_prompt = f"""Bạn là Trợ lý Luật sư ảo chuyên về Bộ Luật Dân Sự 2015 của Việt Nam.
Nhiệm vụ của bạn là trả lời thắc mắc của người dùng dựa trên CÁC ĐIỀU LUẬT ĐƯỢC CUNG CẤP dưới đây.

--- DỮ LIỆU LUẬT (CONTEXT) ---
{context_text}
-------------------------------

HƯỚNG DẪN TRẢ LỜI:
1. Dữ liệu ngữ cảnh có định dạng `[Thuộc Phần... - Chương... - Mục...]` ở đầu mỗi điều luật. Hãy sử dụng thông tin này để trả lời câu hỏi về cấu trúc.
2. KHÔNG ĐƯỢC tự ý bịa đặt tên Chương/Mục nếu không thấy trong ngữ cảnh.
3. Trích dẫn ĐẦY ĐỦ nội dung điều luật.
4. Luôn trích dẫn số điều luật (Ví dụ: "Theo Điều 25...") khi bắt đầu câu trả lời.
5. Giọng điệu chuyên nghiệp, khách quan."""

    from fastapi.responses import StreamingResponse
    import json
    from app.service.local_llm import LocalLLMService

    async def event_generator():
        # 1. Send Sources info first
        yield json.dumps({"type": "sources", "data": sources}, ensure_ascii=False) + "\n"
        
        # 2. Stream AI Content
        llm_service = LocalLLMService()
        try:
            async for chunk in llm_service.generate_response_stream(user_msg, system_prompt):
                # Send text chunk
                # Using a JSON wrapper to keep protocol simple
                if chunk:
                    yield json.dumps({"type": "content", "data": chunk}, ensure_ascii=False) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "data": str(e)}, ensure_ascii=False) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
