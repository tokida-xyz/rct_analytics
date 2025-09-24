#!/bin/bash

# 環境変数の設定
export PYTHONPATH=/app/backend
export PORT=${PORT:-8000}

# ディレクトリの作成
mkdir -p /tmp/uploads /tmp/results

# アプリケーションの起動
cd /app/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
