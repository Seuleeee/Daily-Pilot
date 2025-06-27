# 개발 환경 구축
## 환경변수 설정
 `.env` 파일을 활용해, 환경 변수를 설정합니다. 파일은 `.env.dev`, `.env.stage` 로 나뉩니다.
- 현재 경로에 `.env.dev` 파일을 아래와 같이 생성 합니다.
- 이 파일은 Local 개발환경, Docker 사용시 모두 사용 가능합니다.
- 아래 내용은 예시 이며, `OPENAI_API_KEY`만 넣어주시면, 제대로 동작합니다.
다만, 보안을 고려해 stage 이상 환경에서는 다른 값들을 사용해주세요.


```text
# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=daily-pilot
POSTGRES_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/postgres

# MongoDB
MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_USERNAME=root
MONGODB_PASSWORD=example
MONGODB_URL=mongodb://root:example@mongodb:27017/

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# Mongo Express (웹 UI용)
ME_ADMIN=admin
ME_ADMIN_PASS=adminpass

OPENAI_API_KEY={{Your-API-Key}}
```

## Local 개발 환경
### 패키지 설치
```shell
pip install uv # uv 설치
uv venv .venv  # 가상환경 설치
source .venv/bin/activate # 가상환경 실행
uv sync # 패키지 설치
uv pip install --group dev # 개발 패키지 설치
```
### 서버 실행
```shell
fastapi run src/main.py
```

## Docker Compose
```shell
docker compose -f compose-dev.yml --env-file .env.dev up -d
```
### 실행 확인
#### 1. Backend (RESTful API Server)
- SWAGGER: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### 2. PostgreSQL
- DB 활용 Tool(DBeaver)을 사용해 연결하거나, CLI로 연결을 확인하세요.
- `.env.dev`에 설정한, 값들을 활용해서 접속하세요.

#### 3. MongoDB / Mongo Express
- Mongo Express에 접속해 정상 실행을 확인합니다.
- `.env.dev`에 설정한, 값들을 활용해서 접속하세요.
- `http://localhost:8081`
![alt text](./assets/readme_mongodb.png)

#### 4. Redis
- redis를 설치하세요.
- 아래 명령어를 순차적으로 입력하며, 연결을 확인하세요.
```shell
redis-cli -h localhost -p 6379
ping
SET mykey hello
GET mykey
DEL mykey
```