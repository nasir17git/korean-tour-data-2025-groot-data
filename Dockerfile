# docker build -t nasir17/korean-tour-app-crawler:latest .
FROM python:3.11-slim

# 작업 디렉토리
WORKDIR /app

# 시스템 패키지: CA 인증서 및 OpenSSL 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    openssl \
  && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 복사
COPY . .

# 런타임 기본 환경
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 기본 실행 커맨드(인자로 덮어쓰기 가능)
CMD ["python", "main.py"]


