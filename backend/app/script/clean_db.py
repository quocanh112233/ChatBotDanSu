
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
from app.core.config import get_settings
from app.models.knowledge import KnowledgeBase

load_dotenv(os.path.join(BASE_DIR, ".env"))
settings = get_settings()

# Dùng Sync Engine cho script
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def clean_database():
    session = SessionLocal()
    try:
        print("Đang DROP bảng 'knowledge_base' để tái tạo cấu trúc mới (Vector 384)...")
        KnowledgeBase.__table__.drop(engine)
        print("Đã xóa bảng thành công.")
    except Exception as e:
        if "does not exist" in str(e):
             print("Bảng không tồn tại, bỏ qua.")
        else:
             print(f"Lỗi: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    clean_database()
