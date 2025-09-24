"""
結果取得API
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import logging
from typing import List

from app.models.schemas import AnalysisResult, ErrorResponse
from app.services.job_manager import JobManager
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# ジョブマネージャーのインスタンス
job_manager = JobManager()

@router.get("/result/{job_id}", response_model=AnalysisResult)
async def get_analysis_result(job_id: str):
    """
    分析結果を取得
    
    Args:
        job_id: ジョブID
    
    Returns:
        AnalysisResult: 分析結果
    """
    try:
        job_status = job_manager.get_job_status(job_id)
        if not job_status:
            raise HTTPException(status_code=404, detail="ジョブが見つかりません")
        
        if job_status.status != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"分析が完了していません。現在のステータス: {job_status.status}"
            )
        
        result = job_manager.get_job_result(job_id)
        if not result:
            raise HTTPException(status_code=404, detail="分析結果が見つかりません")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析結果取得エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"結果の取得中にエラーが発生しました: {str(e)}"
        )

@router.get("/download/{job_id}/csv")
async def download_csv_result(job_id: str):
    """
    CSV結果ファイルをダウンロード
    
    Args:
        job_id: ジョブID
    
    Returns:
        FileResponse: CSVファイル
    """
    try:
        csv_path = os.path.join(settings.RESULTS_DIR, job_id, "interaction_summary.csv")
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="CSVファイルが見つかりません")
        
        return FileResponse(
            path=csv_path,
            filename=f"interaction_summary_{job_id}.csv",
            media_type="text/csv"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSVダウンロードエラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"CSVファイルのダウンロード中にエラーが発生しました: {str(e)}"
        )

@router.get("/download/{job_id}/logs")
async def download_logs(job_id: str):
    """
    ログファイルをダウンロード
    
    Args:
        job_id: ジョブID
    
    Returns:
        FileResponse: ログファイル
    """
    try:
        log_path = os.path.join(settings.RESULTS_DIR, job_id, "analysis.log")
        if not os.path.exists(log_path):
            raise HTTPException(status_code=404, detail="ログファイルが見つかりません")
        
        return FileResponse(
            path=log_path,
            filename=f"analysis_log_{job_id}.txt",
            media_type="text/plain"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ログダウンロードエラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ログファイルのダウンロード中にエラーが発生しました: {str(e)}"
        )

@router.get("/download/{job_id}/figs/{figure_name}")
async def download_figure(job_id: str, figure_name: str):
    """
    図ファイルをダウンロード
    
    Args:
        job_id: ジョブID
        figure_name: 図ファイル名
    
    Returns:
        FileResponse: 図ファイル
    """
    try:
        # セキュリティチェック（パストラバーサル攻撃の防止）
        if ".." in figure_name or "/" in figure_name or "\\" in figure_name:
            raise HTTPException(status_code=400, detail="無効なファイル名です")
        
        fig_path = os.path.join(settings.RESULTS_DIR, job_id, "figures", figure_name)
        if not os.path.exists(fig_path):
            raise HTTPException(status_code=404, detail="図ファイルが見つかりません")
        
        # ファイル拡張子に基づいてメディアタイプを決定
        ext = os.path.splitext(figure_name)[1].lower()
        media_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml"
        }
        media_type = media_type_map.get(ext, "application/octet-stream")
        
        return FileResponse(
            path=fig_path,
            filename=figure_name,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"図ダウンロードエラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"図ファイルのダウンロード中にエラーが発生しました: {str(e)}"
        )

@router.get("/result/{job_id}/figures")
async def list_figures(job_id: str):
    """
    利用可能な図ファイルのリストを取得
    
    Args:
        job_id: ジョブID
    
    Returns:
        dict: 図ファイルリスト
    """
    try:
        figures_dir = os.path.join(settings.RESULTS_DIR, job_id, "figures")
        if not os.path.exists(figures_dir):
            return {"figures": []}
        
        figures = []
        for filename in os.listdir(figures_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                figures.append({
                    "name": filename,
                    "url": f"/api/download/{job_id}/figs/{filename}"
                })
        
        return {"figures": figures}
        
    except Exception as e:
        logger.error(f"図リスト取得エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"図リストの取得中にエラーが発生しました: {str(e)}"
        )
