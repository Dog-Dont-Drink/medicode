"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import advanced_analysis, admin, auth, dashboard, datasets, descriptive, payment, polish, projects, reports, users

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(projects.router)
router.include_router(datasets.router)
router.include_router(descriptive.router)
router.include_router(advanced_analysis.router)
router.include_router(polish.router)
router.include_router(dashboard.router)
router.include_router(payment.router)
router.include_router(reports.router)
router.include_router(admin.router)
