"""
FastAPI main application
交互作用検定Webアプリのメインアプリケーション
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api import upload, analysis, results
from app.core.config import settings

# FastAPIアプリケーションの作成
app = FastAPI(
    title="交互作用検定 Webアプリ",
    description="rawデータを読み込み、交互作用検定と要約表・図の自動生成を行うWebアプリケーション",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(results.router, prefix="/api", tags=["results"])

# 静的ファイルの配信
if not os.path.exists("uploads"):
    os.makedirs("uploads")
if not os.path.exists("results"):
    os.makedirs("results")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/results", StaticFiles(directory="results"), name="results")

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "交互作用検定 Webアプリ API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
