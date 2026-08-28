from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.businesses import router as businesses_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.workflows import router as workflows_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(businesses_router)
api_router.include_router(approvals_router)
api_router.include_router(workflows_router)
