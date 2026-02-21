import time
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..auth import authenticate_user, create_access_token, get_current_user_or_fail
from ..settings import settings
from ..database import User, get_db
from .util import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login endpoint - accepts username and password, sets session cookie"""

    # Add delay to mitigate brute-force attacks
    time.sleep(0.5)

    # Authenticate user credentials
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        return error("Incorrect username or password")

    # Update last login info
    user.last_logged_in = datetime.now(timezone.utc)
    user.last_logged_from = request.client.host if request.client else None
    db.commit()

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # Set cookie for browser navigation
    response = success("Login successful")
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax",
        secure=settings.secure_cookies,
    )
    response.headers["HX-Redirect"] = "/"

    logger.info(f"Login: {user.username} from {user.last_logged_from}")
    return response


@router.post("/logout", response_class=HTMLResponse)
async def logout(current_user: User = Depends(get_current_user_or_fail)):
    """Logout endpoint - clears authentication cookie and redirects to login"""
    response = success("Logout successful")
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=settings.secure_cookies,
    )
    response.headers["HX-Redirect"] = "/login"

    logger.info(f"Logout: {current_user.username}")
    return response
