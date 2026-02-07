#!/bin/bash
set -e

echo "🔄 Running database migrations..."
cd /app
python -m alembic upgrade head 2>/dev/null || echo "⚠️ Migrations skipped (may already be up to date)"

echo "🚀 Starting KSAR Backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
