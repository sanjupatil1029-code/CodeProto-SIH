from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.businesses import router as businesses_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.documents import router as documents_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.inspections import router as inspections_router
from app.api.v1.grievances import router as grievances_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(businesses_router)
api_router.include_router(approvals_router)
api_router.include_router(workflows_router)
api_router.include_router(documents_router)
api_router.include_router(compliance_router)
api_router.include_router(inspections_router)
api_router.include_router(grievances_router)
