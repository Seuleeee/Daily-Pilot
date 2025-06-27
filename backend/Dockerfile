FROM python:3.10-slim

WORKDIR /app
ENV TZ=Asia/Seoul

RUN apt-get update && apt-get install -y \
    locales \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# FastAPI CLI 설치
RUN pip install --no-cache-dir fastapi-cli

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock ./
COPY src/ ./src

# 의존성 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

EXPOSE 8000

CMD ["fastapi", "run", "src/main.py"]
