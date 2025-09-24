"""
ファイルアップロードAPI
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import pandas as pd
import uuid
import os
from typing import List
import logging

from app.models.schemas import UploadResponse, ColumnInfo, DataType, ErrorResponse
from app.services.data_processor import DataProcessor
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    ファイルをアップロードし、データの基本情報を返す
    
    Args:
        file: アップロードされたファイル（CSV/XLSX）
    
    Returns:
        UploadResponse: ファイル情報と列情報
    """
    try:
        # ファイル拡張子の検証
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていないファイル形式です。対応形式: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # ファイルサイズの検証
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"ファイルサイズが大きすぎます。最大サイズ: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # ジョブIDの生成
        job_id = str(uuid.uuid4())
        
        # ファイルの保存
        upload_dir = os.path.join(settings.UPLOAD_DIR, job_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # データの読み込みと処理
        data_processor = DataProcessor()
        df, columns_info, preview_data = await data_processor.process_uploaded_file(file_path)
        
        # レスポンスの作成
        response = UploadResponse(
            job_id=job_id,
            filename=file.filename,
            columns=columns_info,
            preview_data=preview_data,
            message="ファイルのアップロードが完了しました"
        )
        
        logger.info(f"ファイルアップロード完了: {file.filename}, ジョブID: {job_id}")
        return response
        
    except Exception as e:
        logger.error(f"ファイルアップロードエラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ファイルの処理中にエラーが発生しました: {str(e)}"
        )

@router.get("/upload/{job_id}/preview")
async def get_data_preview(job_id: str, rows: int = 50):
    """
    アップロードされたデータのプレビューを取得
    
    Args:
        job_id: ジョブID
        rows: 表示する行数
    
    Returns:
        dict: プレビューデータ
    """
    try:
        upload_dir = os.path.join(settings.UPLOAD_DIR, job_id)
        if not os.path.exists(upload_dir):
            raise HTTPException(status_code=404, detail="ジョブが見つかりません")
        
        # ファイルの検索
        files = [f for f in os.listdir(upload_dir) if f.endswith(('.csv', '.xlsx', '.xls'))]
        if not files:
            raise HTTPException(status_code=404, detail="データファイルが見つかりません")
        
        file_path = os.path.join(upload_dir, files[0])
        
        # データの読み込み
        data_processor = DataProcessor()
        df, _, preview_data = await data_processor.process_uploaded_file(file_path, preview_rows=rows)
        
        return {
            "job_id": job_id,
            "preview_data": preview_data,
            "total_rows": len(df),
            "columns": list(df.columns)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"データプレビュー取得エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"データの取得中にエラーが発生しました: {str(e)}"
        )
