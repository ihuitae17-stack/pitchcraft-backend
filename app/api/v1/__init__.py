from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .videos import router as videos_router
from .analyses import router as analyses_router

# v1 API 라우터 통합
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(videos_router)
api_router.include_router(analyses_router)
