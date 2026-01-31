
from fastapi import APIRouter, Depends, Header, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.postgre import get_db
from app.schemas.auth import GoogleLoginPayload, Token, RefreshTokenRequest, User
from app.service.auth_service import AuthService
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

@router.post("/login/google", response_model=User)
async def google_login(
    response: Response,
    payload: GoogleLoginPayload,
    user_agent: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Đăng nhập Google -> Set HttpOnly Cookie -> Trả về User Info (không kèm token).
    """
    auth_service = AuthService(db)
    token_data = await auth_service.login_with_google(payload.credential, user_agent)
    
    # Set HttpOnly Cookies
    response.set_cookie(
        key="access_token",
        value=token_data.access_token,
        httponly=True,
        secure=False, # Set True nếu chạy HTTPS production
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=token_data.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return token_data.user

@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh Token từ Cookie -> Set Cookie mới.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    auth_service = AuthService(db)
    new_token = await auth_service.refresh_token(refresh_token)
    
    # Update Access Token Cookie only (Refresh token usually stays same or rotates)
    response.set_cookie(
        key="access_token",
        value=new_token.access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {"message": "Token refreshed"}

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Đăng xuất -> Xóa Cookie & Session DB.
    """
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        auth_service = AuthService(db)
        await auth_service.logout(refresh_token)
    
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"message": "Logged out successfully"}
