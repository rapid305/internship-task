from fastapi import APIRouter

from app.transactions.api.v1.analytics import router as analytics_router
from app.transactions.api.v1.transactions import router as transactions_router

router = APIRouter(prefix="/v1")
router.include_router(transactions_router)
router.include_router(analytics_router)
