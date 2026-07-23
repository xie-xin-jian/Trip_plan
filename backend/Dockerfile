FROM python:3.10-slim

WORKDIR /app

# 使用清华镜像源
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    fastapi \
    uvicorn[standard] \
    pydantic \
    pydantic-settings \
    httpx \
    aiohttp \
    python-dotenv \
    python-multipart \
    loguru \
    sqlalchemy \
    python-jose[cryptography] \
    passlib \
    email-validator \
    python-dateutil \
    argon2-cffi \
    langgraph \
    langchain \
    langchain-core \
    langchain-openai

# 复制代码
COPY . .

# 创建数据库
RUN python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)" || true

EXPOSE 8001

CMD ["python", "run.py"]