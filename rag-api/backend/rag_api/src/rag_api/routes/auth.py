from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from ..database import get_session
from ..models import User, RefreshToken
from ..schemas import (
    UserCreate, UserResponse, LoginRequest,
    TokenResponse, AccessTokenResponse, ChangePasswordRequest
)
from ..auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Fix 4: Refresh token body mein (URL mein nahi)
class RefreshRequest(BaseModel):
    refresh_token: str

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = session.get(User, int(payload.get("sub")))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(user_data: UserCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == user_data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    # form_data.username mein email aati hai
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    db_token = RefreshToken(token=refresh_token, user_id=user.id)
    session.add(db_token)
    session.commit()
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

# Fix 4: Ab refresh_token body mein aa raha hai (URL mein nahi)
@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(data: RefreshRequest, session: Session = Depends(get_session)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    db_token = session.exec(
        select(RefreshToken).where(RefreshToken.token == data.refresh_token)
    ).first()
    if not db_token or db_token.is_revoked:
        raise HTTPException(status_code=401, detail="Token revoked or not found")
    return AccessTokenResponse(
        access_token=create_access_token({"sub": payload.get("sub")})
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
def logout(data: RefreshRequest, session: Session = Depends(get_session)):
    db_token = session.exec(
        select(RefreshToken).where(RefreshToken.token == data.refresh_token)
    ).first()
    if db_token:
        db_token.is_revoked = True
        session.add(db_token)
        session.commit()
    return {"message": "Logged out successfully"}

# Fix 5: Password change pe saare refresh tokens invalidate
@router.put("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password incorrect")
    
    # Naya password save karo
    current_user.hashed_password = hash_password(data.new_password)
    session.add(current_user)
    
    # Fix 5: Is user ke SAARE refresh tokens revoke karo
    all_tokens = session.exec(
        select(RefreshToken).where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False
        )
    ).all()
    
    for token in all_tokens:
        token.is_revoked = True
        session.add(token)
    
    session.commit()
    return {"message": f"Password changed. {len(all_tokens)} session(s) invalidated."}