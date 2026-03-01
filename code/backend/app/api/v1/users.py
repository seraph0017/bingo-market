"""Users API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_current_user():
    """Get current user profile."""
    return {"message": "TODO: Implement user profile"}


@router.put("/me/password")
async def change_password():
    """Change password."""
    return {"message": "TODO: Implement password change"}
