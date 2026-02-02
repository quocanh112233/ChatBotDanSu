
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User, Session
from app.schemas.auth import User as UserSchema, Token
from app.core.security import create_access_token, create_refresh_token, verify_token_data
from app.core.config import get_settings
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import uuid

settings = get_settings()

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_google_token(self, token: str) -> dict:
        """
        Verify Google ID Token bằng cách gọi Google Api Endpoint.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(GOOGLE_TOKEN_INFO_URL, params={"id_token": token})
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail="Invalid Google Token")
                
                data = response.json()
                
                # Kiểm tra aud (audience) xem có khớp client_id không (nếu có cấu hình)
                if settings.GOOGLE_CLIENT_ID and data.get("aud") != settings.GOOGLE_CLIENT_ID:
                     raise HTTPException(status_code=400, detail="Token audience mismatch")
                
                return data
            except httpx.RequestError:
                 raise HTTPException(status_code=503, detail="Could not verify token with Google")

    async def get_or_create_user(self, google_data: dict) -> User:
        email = google_data.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email not found in Google Token")

        # Check user exist
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user:
            # Create new user
            user = User(
                email=email,
                full_name=google_data.get("name"),
                avatar_url=google_data.get("picture"),
                is_active=True
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
        
        return user


    async def create_user_session(self, user: User, user_agent: str = None) -> Token:
        # Create tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        

        # Save session to DB
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        session = Session(
            user_id=user.id,
            refresh_token=refresh_token,
            user_agent=user_agent,
            expires_at=expires_at
        )
        self.db.add(session)
        await self.db.commit()

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserSchema.model_validate(user)
        )

    async def login_with_google(self, token: str, user_agent: str = None) -> Token:
        google_data = await self.verify_google_token(token)
        user = await self.get_or_create_user(google_data)
        token_data = await self.create_user_session(user, user_agent)
        return token_data

    async def refresh_token(self, refresh_token: str) -> Token:
        # Verify JWT structure
        payload = verify_token_data(refresh_token)
        if not payload or payload.get("type") != "refresh":
             raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user_id = payload.get("sub")
        
        # Check DB session
        stmt = select(Session).where(Session.refresh_token == refresh_token)
        result = await self.db.execute(stmt)
        session_record = result.scalars().first()
        
        if not session_record:
             raise HTTPException(status_code=401, detail="Session not found or revoked")
            
        if session_record.expires_at.replace(tzinfo=None) < datetime.utcnow():
            # Xóa session hết hạn
            await self.db.delete(session_record)
            await self.db.commit()
            raise HTTPException(status_code=401, detail="Refresh token expired")

        # Generate new Access Token
        new_access_token = create_access_token(subject=user_id)
        
        # Lấy thông tin user
        user_stmt = select(User).where(User.id == uuid.UUID(user_id))
        user_res = await self.db.execute(user_stmt)
        user = user_res.scalars().first()

        return Token(
            access_token=new_access_token,
            refresh_token=refresh_token, # Keep old refresh token or rotate? Giữ nguyên cho đơn giản
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserSchema.model_validate(user)
        )

    async def logout(self, refresh_token: str):
        stmt = select(Session).where(Session.refresh_token == refresh_token)
        result = await self.db.execute(stmt)
        session = result.scalars().first()
        if session:
            await self.db.delete(session)
            await self.db.commit()
