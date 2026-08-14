# 应用镜像 —— 通过多级构建引用语料库数据镜像
# 数据镜像需先构建好：backend/data-image 目录下 docker build -t cookbook/corpus:latest .
FROM cookbook/corpus:latest AS corpus

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    IMPORT_DATA_DIR=/data

COPY pyproject.toml ./
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple .

COPY . .

# 从数据镜像复制语料库
COPY --from=corpus /data/recipe_corpus_full.json.gz /data/recipe_corpus_full.json.gz

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
