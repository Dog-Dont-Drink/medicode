"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, dashboard, datasets, payment, projects, users

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(projects.router)
router.include_router(datasets.router)
router.include_router(dashboard.router)
router.include_router(payment.router)
