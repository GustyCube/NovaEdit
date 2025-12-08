FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src
COPY model /app/model

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[train]" uvicorn

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["uvicorn", "novaedit.server.main:app", "--host", "0.0.0.0", "--port", "8000"]
