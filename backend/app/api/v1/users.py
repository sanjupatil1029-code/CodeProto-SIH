from fastapi import APIRouter, Depends
from app.models.auth import User, UserRole
from app.schemas.auth import UserOut
from app.services.auth_service import get_current_user, RoleChecker

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the currently authenticated user's profile."""
    return current_user


@router.get("/admin-only", response_model=UserOut)
async def test_admin_route(
    current_user: User = Depends(RoleChecker([UserRole.ADMIN]))
):
    """Admin-only resource (for testing RBAC)."""
    return current_user


@router.get("/officer-only", response_model=UserOut)
async def test_officer_route(
    current_user: User = Depends(RoleChecker([UserRole.OFFICER, UserRole.ADMIN]))
):
    """Officer-only resource (for testing RBAC)."""
    return current_user
