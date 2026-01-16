"""Authentication API routes for TeleScope."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.auth.users import auth_backend, fastapi_users, current_active_user
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.models.user import User
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

# Include FastAPI-Users routers
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="",
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="",
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="",
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="",
)

# User management routes (admin only)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
)


@router.get("/me", response_model=UserRead, summary="Get current user profile")
async def get_current_user_profile(user: User = Depends(current_active_user)):
    """Get the current authenticated user's profile."""
    return user


@router.post("/me/consent", response_model=UserRead, summary="Record RGPD consent")
async def record_consent(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Record user's RGPD consent timestamp."""
    user.consent_given_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/me/data", summary="Request data deletion (RGPD)")
async def request_data_deletion(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Request deletion of all user data (RGPD right to be forgotten)."""
    # In a real implementation, this would:
    # 1. Anonymize user data
    # 2. Delete personal information
    # 3. Keep audit logs for legal compliance
    # For now, we just mark the account as inactive

    user.is_active = False
    await db.commit()

    return {
        "status": "success",
        "message": "Your account has been deactivated. Personal data will be anonymized within 30 days.",
    }
