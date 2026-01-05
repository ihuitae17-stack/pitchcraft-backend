from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, videos, analyses

# FastAPI 앱 생성
app = FastAPI(
    title="PitchCraft API",
    description="AI 기반 투구폼 분석 서비스",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(auth.router, prefix="/api/v1")
app.include_router(videos.router, prefix="/api/v1")
app.include_router(analyses.router, prefix="/api/v1")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": "PitchCraft API",
        "version": "1.0.0",
        "status": "running",
        "message": "🚀 PitchCraft Backend is live!",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy"}


@app.get("/api/v1/test")
async def test_endpoint():
    """테스트 API 엔드포인트"""
    return {
        "message": "API is working!",
        "features": [
            "User authentication",
            "Video upload",
            "Pitch analysis"
        ]
    }

