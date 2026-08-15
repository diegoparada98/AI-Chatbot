# --- Stage 1: build the React SPA --------------------------------------
FROM node:22-alpine AS frontend
# Optional escape hatch for TLS-intercepting proxy/AV machines: pass
# --build-arg NPM_STRICT_SSL=false. Defaults to secure (true) for cloud builds.
ARG NPM_STRICT_SSL=true
ENV NPM_CONFIG_STRICT_SSL=${NPM_STRICT_SSL}
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build          # -> /frontend/dist

# --- Stage 2: Python backend serving API + the built SPA ---------------
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Optional: for builds behind a TLS-intercepting proxy/AV (e.g. corporate laptop),
# pass --build-arg PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org".
# Left empty by default so cloud builds stay fully certificate-verified.
ARG PIP_TRUSTED_HOST=""
ENV PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}

# Install backend deps first (better layer caching).
COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/app /app/backend/app
RUN pip install /app/backend

# Bring in the compiled frontend where main.py expects it (/app/frontend/dist).
COPY --from=frontend /frontend/dist /app/frontend/dist

WORKDIR /app/backend
EXPOSE 8000

# Railway/most PaaS inject $PORT; default to 8000 locally. Shell form so it expands.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
