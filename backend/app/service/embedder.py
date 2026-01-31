import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class Embedder:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        self.model = 'models/embedding-001'

    def embed_query(self, text: str):
        """Chuyển đổi một câu truy vấn thành vector"""
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']

    def embed_documents(self, texts: list[str]):
        """Chuyển đổi danh sách văn bản thành danh sách vector"""
        result = genai.embed_content(
            model=self.model,
            content=texts,
            task_type="retrieval_document"
        )
        return result['embedding']

# Khởi tạo instance dùng chung
embedder = Embedder()
