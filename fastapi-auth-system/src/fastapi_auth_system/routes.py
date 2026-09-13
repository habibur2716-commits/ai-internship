from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from .database import get_session
from .models import User, RefreshToken
from .schemas import (
    UserCreate, UserResponse, LoginRequest,
    TokenResponse, AccessTokenResponse,
    ChangePasswordRequest
)
from .auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ============ HELPER: Current User Nikalna ============

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    user_id = payload.get("sub")
    user = session.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ============ SIGNUP ============

@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(user_data: UserCreate, session: Session = Depends(get_session)):
    # Email already exist karta hai?
    existing = session.exec(select(User).where(User.email == user_data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Password hash karo
    hashed = hash_password(user_data.password)
    
    # User banao
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

# ============ LOGIN ============

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, session: Session = Depends(get_session)):
    # User dhoondo
    user = session.exec(select(User).where(User.email == login_data.email)).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Tokens banao
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    # Refresh token database mein save karo
    db_token = RefreshToken(token=refresh_token, user_id=user.id)
    session.add(db_token)
    session.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

# ============ REFRESH TOKEN ============

@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_token(refresh_token: str, session: Session = Depends(get_session)):
    # Token verify karo
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Database mein check karo - revoked toh nahi?
    db_token = session.exec(
        select(RefreshToken).where(RefreshToken.token == refresh_token)
    ).first()
    
    if not db_token or db_token.is_revoked:
        raise HTTPException(status_code=401, detail="Refresh token revoked or not found")
    
    # Naya access token banao
    user_id = payload.get("sub")
    new_access_token = create_access_token({"sub": user_id})
    
    return AccessTokenResponse(access_token=new_access_token)

# ============ GET CURRENT USER (Protected) ============

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ============ LOGOUT ============

@router.post("/logout")
def logout(refresh_token: str, session: Session = Depends(get_session)):
    db_token = session.exec(
        select(RefreshToken).where(RefreshToken.token == refresh_token)
    ).first()
    
    if db_token:
        db_token.is_revoked = True
        session.add(db_token)
        session.commit()
    
    return {"message": "Logged out successfully"}

# ============ CHANGE PASSWORD ============

@router.put("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Purana password verify karo
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Naya password hash karo aur save karo
    current_user.hashed_password = hash_password(data.new_password)
    session.add(current_user)
    session.commit()
    
    return {"message": "Password changed successfully"}