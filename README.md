# PitchCraft Backend

AI 기반 투구폼 분석 서비스의 백엔드 서버입니다.

## 기술 스택

- **FastAPI** - 고성능 비동기 웹 프레임워크
- **PostgreSQL** - 관계형 데이터베이스
- **Redis** - 캐시 및 메시지 브로커
- **Celery** - 분산 작업 큐
- **Docker Compose** - 로컬 개발 환경

## 빠른 시작

### 1. 환경 변수 설정

```bash
cp .env.example .env
```

### 2. Docker Compose로 실행

```bash
docker-compose up -d
```

### 3. API 확인

- API 문서: <http://localhost:8000/docs>
- 헬스체크: <http://localhost:8000/health>

## API 엔드포인트

### 인증

- `POST /api/v1/auth/register` - 회원가입
- `POST /api/v1/auth/login` - 로그인

### 사용자

- `GET /api/v1/users/me` - 내 정보 조회
- `PATCH /api/v1/users/me` - 내 정보 수정

### 영상

- `POST /api/v1/videos/upload-request` - 업로드 URL 요청
- `POST /api/v1/videos/{video_id}/upload-complete` - 업로드 완료 확인
- `GET /api/v1/videos` - 영상 목록 조회
- `GET /api/v1/videos/{video_id}` - 영상 상세 조회

### 분석

- `POST /api/v1/analyses` - 분석 요청
- `GET /api/v1/analyses` - 분석 결과 목록
- `GET /api/v1/analyses/{analysis_id}` - 분석 결과 상세

## 개발 가이드

### 로컬 개발 (Docker 없이)

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload
```

### 마이그레이션

```bash
# Alembic 초기화 (최초 1회)
alembic init alembic

# 마이그레이션 생성
alembic revision --autogenerate -m "Initial"

# 마이그레이션 적용
alembic upgrade head
```

## 배포

Railway에 배포할 때는 환경 변수만 설정하면 자동 배포됩니다.

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인 및 배포
railway login
railway up
```

## 라이선스

MIT License
