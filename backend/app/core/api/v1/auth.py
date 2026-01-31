
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.postgre import get_db
from app.schemas.auth import GoogleLoginPayload, Token, RefreshTokenRequest
from app.service.auth_service import AuthService

router = APIRouter()

@router.post("/login/google", response_model=Token)
async def google_login(
    payload: GoogleLoginPayload,
    user_agent: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Đăng nhập bằng Google ID Token nhận từ Frontend.
    Nếu user chưa tồn tại sẽ tự động tạo mới.
    Trả về Access Token và Refresh Token.
    """
    auth_service = AuthService(db)
    token_data = await auth_service.login_with_google(payload.credential, user_agent)
    return token_data

@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy Access Token mới bằng Refresh Token.
    """
    auth_service = AuthService(db)
    new_token = await auth_service.refresh_token(payload.refresh_token)
    return new_token

@router.post("/logout")
async def logout(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Đăng xuất: Xóa session tương ứng với refresh token.
    """
    auth_service = AuthService(db)
    await auth_service.logout(payload.refresh_token)
    return {"message": "Logged out successfully"}
