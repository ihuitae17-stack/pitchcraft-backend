from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.database import init_db
from app.api.v1 import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 이벤트"""
    # 시작 시: 데이터베이스 테이블 생성 시도
    try:
        await init_db()
        print("✅ Database connected successfully!")
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        print("📌 App will start without database. Configure DATABASE_URL to enable full features.")
    
    print("🚀 PitchCraft Backend Server Started!")
    yield
    # 종료 시
    print("👋 PitchCraft Backend Server Stopped!")


# FastAPI 앱 생성
app = FastAPI(
    title="PitchCraft API",
    description="AI 기반 투구폼 분석 서비스",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": "PitchCraft API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy"}
