FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=20 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    DATA_DIR=/app/data \
    LOG_DIR=/app/logs

WORKDIR /app

RUN sed -i \
        -e 's|http://deb.debian.org/debian-security|http://mirrors.aliyun.com/debian-security|g' \
        -e 's|http://deb.debian.org/debian|http://mirrors.aliyun.com/debian|g' \
        /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Retries=5 update \
    && apt-get -o Acquire::Retries=5 install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY data/catalog ./data/catalog

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install ".[backtrader,easytrader,qbot,ai-quant,tradingagents]" --progress-bar off

RUN mkdir -p /app/data/simulation_reviews /app/logs

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=5)"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
