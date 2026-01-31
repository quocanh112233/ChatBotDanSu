
import uuid
from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.database.postgre import Base

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, index=True) # VD: "Bộ Luật Dân Sự 2015"
    chunk_id = Column(String) # VD: "Dieu_1"
    content = Column(Text, nullable=False) # Nội dung điều luật
    embedding = Column(Vector(384)) # Vector embedding từ MiniLM (384 dimensions)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
