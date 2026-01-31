
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional

# Schema dữ liệu nhận từ Frontend khi login Google
class GoogleLoginPayload(BaseModel):
    credential: str # Google ID Token

# Schema thông tin User trả về
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True

# Schema Token trả về (Access + Refresh)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    expires_in: int # seconds
    user: UserResponse

# Schema Refresh Token Request
class RefreshTokenRequest(BaseModel):
    refresh_token: str
