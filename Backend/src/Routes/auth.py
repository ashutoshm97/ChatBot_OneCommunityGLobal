from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Authentication.supabase_client import supabase

router = APIRouter(prefix="/auth", tags=["auth"])

class AuthModel(BaseModel):
    email: str
    password: str

# Signup endpoint
@router.post("/signup")
async def signup(auth: AuthModel):
    try:
        user = supabase.auth.sign_up({
            "email": auth.email,
            "password": auth.password
        })
        if user.user is None:
            raise HTTPException(status_code=400, detail=user.message)
        return {"message": "User signed up successfully", "user": user.user.email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Login endpoint
@router.post("/login")
async def login(auth: AuthModel):
    try:
        user = supabase.auth.sign_in({
            "email": auth.email,
            "password": auth.password
        })
        if user.session is None:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        return {
            "message": "Login successful",
            "access_token": user.session.access_token,
            "refresh_token": user.session.refresh_token,
            "expires_at": user.session.expires_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# logout endpoint
@router.post("/logout")
async def logout(access_token: str):
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))