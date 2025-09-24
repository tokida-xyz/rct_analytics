#!/bin/bash

# 交互作用検定Webアプリのセットアップスクリプト

echo "交互作用検定Webアプリのセットアップを開始します..."

# バックエンドのセットアップ
echo "バックエンドのセットアップ中..."
cd backend

# Python仮想環境の作成
if [ ! -d "venv" ]; then
    echo "Python仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境のアクティベート
source venv/bin/activate

# 依存関係のインストール
echo "Python依存関係をインストール中..."
pip install -r requirements.txt

# ディレクトリの作成
mkdir -p uploads results

cd ..

# フロントエンドのセットアップ
echo "フロントエンドのセットアップ中..."
cd frontend

# Node.js依存関係のインストール
echo "Node.js依存関係をインストール中..."
npm install

cd ..

echo "セットアップが完了しました！"
echo ""
echo "開発サーバーを起動するには:"
echo "1. バックエンド: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "2. フロントエンド: cd frontend && npm run dev"
echo ""
echo "または、Docker Composeを使用:"
echo "docker-compose up --build"
