import random
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select, desc
from pydantic import BaseModel, EmailStr
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from ..database import get_session
from ..models import User, RefreshToken, OTPCode
from ..schemas import (
    UserCreate, UserResponse, LoginRequest,
    TokenResponse, AccessTokenResponse, ChangePasswordRequest
)
from ..auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Email Config (SMTP Settings .env se le raha hai)
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "your_email@gmail.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "your_app_password"),
    MAIL_FROM=os.getenv("MAIL_FROM", "your_email@gmail.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Schemas for OTP Operations
class RefreshRequest(BaseModel):
    refresh_token: str

class SendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str  # "signup" or "forgot_password"

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str
    purpose: str

class ResetPasswordOTPRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

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

# Helper function to send email via background task
def send_otp_email_task(email: str, otp: str):
    message = MessageSchema(
        subject="Your Verification Code",
        recipients=[email],
        body=f"Your OTP Code is: {otp}. It will expire in 10 minutes.",
        subtype=MessageType.plain
    )
    fm = FastMail(conf)
    import asyncio
    asyncio.run(fm.send_message(message))

# ==================== OTP ENDPOINTS ====================

@router.post("/send-otp")
def send_otp(
    data: SendOTPRequest, 
    background_tasks: BackgroundTasks, 
    session: Session = Depends(get_session)
):
    clean_email = data.email.strip().lower()

    # If forgot password, ensure user exists
    if data.purpose == "forgot_password":
        user = session.exec(select(User).where(User.email == clean_email)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User with this email does not exist.")

    # Generate 6-digit OTP
    otp_str = f"{random.randint(100000, 999999)}"
    expires = datetime.utcnow() + timedelta(minutes=10)

    otp_record = OTPCode(
        email=clean_email,
        code=otp_str,
        purpose=data.purpose,
        expires_at=expires,
        is_used=False
    )
    session.add(otp_record)
    session.commit()

    # Send Email asynchronously
    background_tasks.add_task(send_otp_email_task, clean_email, otp_str)

    return {"message": "OTP has been sent to your email."}

@router.post("/verify-otp")
def verify_otp(data: VerifyOTPRequest, session: Session = Depends(get_session)):
    clean_email = data.email.strip().lower()
    clean_code = str(data.code).strip()

    otp_record = session.exec(
        select(OTPCode).where(
            OTPCode.email == clean_email,
            OTPCode.code == clean_code,
            OTPCode.purpose == data.purpose,
            OTPCode.is_used == False,
            OTPCode.expires_at > datetime.utcnow()
        ).order_by(desc(OTPCode.expires_at))
    ).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    otp_record.is_used = True
    session.add(otp_record)

    # If it's signup, mark user as verified if exists
    if data.purpose == "signup":
        user = session.exec(select(User).where(User.email == clean_email)).first()
        if user:
            user.is_verified = True
            session.add(user)

    session.commit()
    return {"message": "OTP verified successfully."}

@router.post("/reset-password-otp")
def reset_password_otp(data: ResetPasswordOTPRequest, session: Session = Depends(get_session)):
    clean_email = data.email.strip().lower()
    clean_code = str(data.code).strip()

    # Check if user exists
    user = session.exec(select(User).where(User.email == clean_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Verify OTP (Checks both cases: recently verified OR valid unverified OTP)
    otp_record = session.exec(
        select(OTPCode).where(
            OTPCode.email == clean_email,
            OTPCode.code == clean_code,
            OTPCode.purpose == "forgot_password",
            OTPCode.expires_at > datetime.utcnow()
        ).order_by(desc(OTPCode.expires_at))
    ).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    # Mark OTP as used now
    otp_record.is_used = True
    session.add(otp_record)

    # Update password
    user.hashed_password = hash_password(data.new_password)
    session.add(user)

    # Invalidate all refresh tokens for security
    all_tokens = session.exec(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    ).all()
    for token in all_tokens:
        token.is_revoked = True
        session.add(token)

    session.commit()
    return {"message": "Password reset successfully. You can now login."}

# ==================== EXISTING ENDPOINTS ====================

@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(user_data: UserCreate, session: Session = Depends(get_session)):
    clean_email = user_data.email.strip().lower()
    existing = session.exec(select(User).where(User.email == clean_email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(
        name=user_data.name,
        email=clean_email,
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
    clean_email = form_data.username.strip().lower()
    user = session.exec(select(User).where(User.email == clean_email)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    db_token = RefreshToken(token=refresh_token, user_id=user.id)
    session.add(db_token)
    session.commit()
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

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

@router.put("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password incorrect")
    
    current_user.hashed_password = hash_password(data.new_password)
    session.add(current_user)
    
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