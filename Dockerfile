FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git nodejs npm \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g opencode-ai

COPY requirements.txt pyproject.toml ./
COPY requirements ./requirements
RUN pip install -r requirements.txt
RUN python -m venv /opt/venvs/langgraph \
    && /opt/venvs/langgraph/bin/pip install --no-cache-dir -r requirements/langgraph.txt
RUN python -m venv /opt/venvs/crewai \
    && /opt/venvs/crewai/bin/pip install --no-cache-dir -r requirements/crewai.txt
RUN python -m venv /opt/venvs/maf \
    && /opt/venvs/maf/bin/pip install --no-cache-dir -r requirements/maf.txt

COPY src ./src
RUN pip install -e . --no-deps

COPY README.md ./
COPY REPORT.md ./

ENV PYTHONPATH=/app/src \
    BENCH_LANGGRAPH_PYTHON=/opt/venvs/langgraph/bin/python \
    BENCH_CREWAI_PYTHON=/opt/venvs/crewai/bin/python \
    BENCH_MAF_PYTHON=/opt/venvs/maf/bin/python
ENTRYPOINT ["python", "-m", "bench.cli"]
