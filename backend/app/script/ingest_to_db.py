
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Add parent directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from app.script.preprocess_data import process_file
from app.models.knowledge import KnowledgeBase
from app.core.config import get_settings

load_dotenv(os.path.join(BASE_DIR, ".env"))
settings = get_settings()

# DB Connection
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Load Local Model (MiniLM - 384 dimensions)
print("Đang tải model embedding (chỉ mất vài giây)...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2') 
print("Model đã sẵn sàng!")

def init_db():
    """Tạo extension vector và bảng nếu chưa có"""
    print("--- Khởi tạo Database ---")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Create tables (sẽ tạo lại bảng với cột Vector 384 nếu vừa bị Drop)
    KnowledgeBase.metadata.create_all(bind=engine)
    print("Đã đảm bảo bảng knowledge_base tồn tại.")

def get_embedding(text):
    """Lấy embedding từ local model"""
    # model.encode trả về numpy array, cần convert sang list cho pgvector
    embedding = model.encode(text) 
    return embedding.tolist()

def ingest_data():
    session = SessionLocal()
    try:
        # 1. Load Data
        pdf_path = os.path.join(BASE_DIR, "backend", "data", "raw", "LuatDanSu2015.pdf")
        if not os.path.exists(pdf_path):
             pdf_path = os.path.join(BASE_DIR, "data", "raw", "LuatDanSu2015.pdf")     
        
        # --- DATA INTEGRITY CHECK ---
        from app.script.get_file_hash import calculate_file_hash
        print("Đang kiểm tra tính toàn vẹn dữ liệu...")
        current_hash = calculate_file_hash(pdf_path)
        expected_hash = settings.DATA_INTEGRITY_HASH
        
        if current_hash != expected_hash:
            print("\n" + "="*50)
            print("CẢNH BÁO AN NINH: FILE DỮ LIỆU ĐÃ BỊ THAY ĐỔI!")
            print(f"Hash hiện tại: {current_hash}")
            print(f"Hash gốc     : {expected_hash}")
            print("Hệ thống từ chối import để bảo đảm an toàn.")
            print("="*50 + "\n")
            return
        else:
            print(">> Kiểm tra Hash thành công. Dữ liệu nguyên vẹn.")
        # ----------------------------

        print(f"Đọc dữ liệu từ: {pdf_path}")
        chunks = process_file(pdf_path)
        
        if not chunks:
            print("Không có dữ liệu để import.")
            return

        print(f"\nBắt đầu Embedding {len(chunks)} điều luật bằng Local Model...")
        
        for index, content in enumerate(chunks):
            # Extract title (Find the line starting with "Điều ...")
            # Because now content might start with "[Thuộc ...]"
            lines = content.split('\n')
            chunk_id = f"Article_{index+1}" # default
            
            for line in lines:
                if line.strip().lower().startswith("điều"):
                     # Lấy "Điều 1" từ "Điều 1. Phạm vi..."
                     chunk_id = line.split('.')[0].replace(" ", "_").strip()
                     break
            
            # Fallback nếu tên quá dài (do lỗi cắt)
            if len(chunk_id) > 20:
                chunk_id = f"Article_{index+1}"

            # Check if exists
            exists = session.query(KnowledgeBase).filter_by(chunk_id=chunk_id).first()
            if exists:
                # print(f"Bỏ qua {chunk_id} (đã tồn tại)")
                continue

            # Get Embedding (Local - Siêu nhanh)
            vector = get_embedding(content)
            
            kb_item = KnowledgeBase(
                source="Bộ Luật Dân Sự 2015",
                chunk_id=chunk_id,
                content=content,
                embedding=vector
            )
            session.add(kb_item)
            
            if (index + 1) % 50 == 0:
                print(f"Đã lưu {index + 1}/{len(chunks)} điều...")
                session.commit()
        
        session.commit()
        print("\nHOÀN TẤT IMPORT DỮ LIỆU! (Local Embedding)")
        
    except Exception as e:
        print(f"Lỗi: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
    ingest_data()
