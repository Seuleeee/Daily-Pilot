# 개발 환경 구축
## 환경변수 설정
프로젝트 root 경로에 `.env` 파일을 생성합니다.
test 환경에서는 연결 대상의 주소를 localhost로 사용합니다.

* `{project-root}/.env.dev`(예시) : 개발환경에서 사용
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
* `{project-root}/.env.test`(예시) : 테스트 환경 (pytest) 에서 사용
    ```text
    PYTHON_ENV=test
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=postgres
    POSTGRES_DB=test_db
    POSTGRES_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/test_db

    MONGODB_HOST=localhost
    MONGODB_PORT=27017
    MONGODB_USERNAME=root
    MONGODB_PASSWORD=example
    MONGODB_URL=mongodb://root:example@localhost:27017/

    REDIS_HOST=localhost
    REDIS_PORT=6379
    REDIS_URL=redis://localhost:6379/0

    ME_ADMIN=admin
    ME_ADMIN_PASS=adminpass

    OPENAI_API_KEY=dummy-key
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

### pre-commit-hook 적용
소스 코드 품질 관리를 위해 Lint 검사와 Pytest 실행 도구로써 활용합니다.
```shell
pre-commit install # Project Root에서 실행
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
![Mongo Express](../assets/readme_mongodb.png)

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

## 테스트
### 직접 실행
```
PYTHON_ENV=test pytest -s tests # 현재 경로 실행
PYTHON_ENV=test pytest -s backend/tests # Project Root에서 실행
```
### commit시 실행
pre-commit-hook 에 명시되어 pytest가 자동으로 적용 됩니다.