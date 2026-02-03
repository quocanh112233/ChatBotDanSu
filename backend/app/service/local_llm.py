
import httpx
import json
from app.core.config import get_settings

settings = get_settings()

class LocalLLMService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LOCAL_MODEL_NAME

    async def generate_response(self, prompt: str, system_message: str = None) -> str:
        # Non-streaming fallback (giữ lại cho tương thích nếu cần)
        url = f"{self.base_url}/api/chat"
        messages = self._build_messages(prompt, system_message)
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "repeat_penalty": 1.2,
                "num_predict": 512
            }
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json().get("message", {}).get("content", "")
            except Exception as e:
                print(f"Ollama Error: {e}")
                return "Error generating response."

    async def generate_response_stream(self, prompt: str, system_message: str = None):
        """Generator trả về từng chunk text"""
        url = f"{self.base_url}/api/chat"
        messages = self._build_messages(prompt, system_message)
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True, # ENABLE STREAM
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "repeat_penalty": 1.2,
                "num_predict": 512
            }
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                json_chunk = json.loads(line)
                                msg_content = json_chunk.get("message", {}).get("content", "")
                                if msg_content:
                                    yield msg_content
                                if json_chunk.get("done", False):
                                    break
                            except:
                                pass
            except Exception as e:
                print(f"Stream Error: {e}")
                yield f"[Lỗi kết nối AI: {e}]"

    def _build_messages(self, prompt, system_message):
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        return messages
