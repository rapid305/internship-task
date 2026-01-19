from fastapi import APIRouter

from app.users.api.v1.auth import router as auth_router
from app.users.api.v1.users import router as users_router

router = APIRouter(prefix="/v1")
router.include_router(users_router)
router.include_router(auth_router)
