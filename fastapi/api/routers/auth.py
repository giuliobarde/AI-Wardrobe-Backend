from fastapi import APIRouter, Depends, HTTPException, status
import logging
from typing import Optional

from api.models import SignupUser, SigninUser
from api.Database.auth import (
    sign_up_db,
    sign_in_db,
    get_session_db,
    sign_out_db,
    get_current_user
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="",
    tags=["authentication"]
)

@router.post("/sign-up/", status_code=status.HTTP_201_CREATED)
async def sign_up(user: SignupUser):
    try:
        return sign_up_db(user)
    except Exception as e:
        logger.error(f"Sign-up error: {e}", exc_info=True)
        if "already registered" in str(e).lower():
            raise HTTPException(status.HTTP_409_CONFLICT, "User already exists")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Registration failed")

@router.post("/sign-in/")
async def sign_in(user: SigninUser):
    try:
        return sign_in_db(user)
    except Exception as e:
        logger.error(f"Sign-in error: {e}", exc_info=True)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

@router.get("/session/")
async def get_session(user=Depends(get_current_user)):
    return get_session_db(user)

@router.post("/sign-out/")
async def sign_out(user=Depends(get_current_user)):
    return sign_out_db(user) 