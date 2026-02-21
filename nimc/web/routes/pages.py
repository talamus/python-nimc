from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..auth import get_current_user
from ..database import User

router = APIRouter(tags=["pages"])

# Templates will be configured in main.py
templates = None


def set_templates(jinja2_templates: Jinja2Templates):
    """Set the Jinja2Templates instance"""
    global templates
    templates = jinja2_templates


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - redirects to login or dashboard"""
    # Check if user has token in cookie/header, redirect accordingly
    # For now, just redirect to login
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    """Dashboard page - requires authentication"""
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": current_user}
    )
