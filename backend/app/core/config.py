"""
アプリケーション設定
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """アプリケーション設定クラス"""
    
    # アプリケーション設定
    APP_NAME: str = "交互作用検定 Webアプリ"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # サーバー設定
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS設定
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://rct-analytics.vercel.app",
        "https://*.vercel.app"
    ]
    
    # ファイルアップロード設定
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]
    UPLOAD_DIR: str = "uploads"
    RESULTS_DIR: str = "results"
    
    # 統計分析設定
    DEFAULT_FDR_ALPHA: float = 0.05
    MIN_SAMPLE_SIZE: int = 30
    MAX_CORRELATION_THRESHOLD: float = 0.9
    
    # セキュリティ設定
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 設定インスタンス
settings = Settings()
