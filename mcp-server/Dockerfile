FROM python:3.12-slim AS base

WORKDIR /app

COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp-server/ .
COPY THIRD_PARTY_NOTICES.txt /usr/share/jpilot/THIRD_PARTY_NOTICES.txt

EXPOSE 8001

FROM base AS dev
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

FROM base AS prod
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8001"]
