from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import Token, UserResponse, UserLogin
from app.auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/demo-users")
def list_demo_users(db: Session = Depends(get_db)):
    """Returns pre-configured demo user accounts for easy role switching in the UI"""
    users = db.query(User).all()
    return [
        {
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "description": {
                "admin": "Full system control, materials, users, settings",
                "store_manager": "Approve transactions, inventory control, audit & reports",
                "store_employee": "Record inward receipts, contractor issues & returns",
                "management": "Executive dashboard, read-only analytics & reporting"
            }.get(u.role, "")
        }
        for u in users
    ]
