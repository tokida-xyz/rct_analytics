"""
分析実行API
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
import logging
from datetime import datetime

from app.models.schemas import AnalysisRequest, JobStatus, AnalysisStatus, ErrorResponse
from app.services.analysis_engine import AnalysisEngine
from app.services.job_manager import JobManager
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# ジョブマネージャーのインスタンス
job_manager = JobManager()

@router.post("/run", response_model=JobStatus)
async def run_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    交互作用検定分析を実行
    
    Args:
        request: 分析リクエスト
        background_tasks: バックグラウンドタスク
    
    Returns:
        JobStatus: ジョブステータス
    """
    try:
        # ジョブの作成
        job_status = JobStatus(
            job_id=request.job_id,
            status=AnalysisStatus.PENDING,
            message="分析を開始しています...",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # ジョブマネージャーに登録
        job_manager.create_job(job_status)
        
        # バックグラウンドで分析を実行
        background_tasks.add_task(
            execute_analysis,
            request.job_id,
            request.settings
        )
        
        logger.info(f"分析ジョブ開始: {request.job_id}")
        return job_status
        
    except Exception as e:
        logger.error(f"分析開始エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"分析の開始中にエラーが発生しました: {str(e)}"
        )

async def execute_analysis(job_id: str, settings):
    """
    分析を実行するバックグラウンドタスク
    
    Args:
        job_id: ジョブID
        settings: 分析設定
    """
    try:
        # ジョブステータスを更新
        job_manager.update_job_status(
            job_id, 
            AnalysisStatus.RUNNING, 
            "分析を実行中...",
            progress=0.1
        )
        
        # 分析エンジンの実行
        analysis_engine = AnalysisEngine()
        result = await analysis_engine.run_analysis(job_id, settings)
        
        # 完了ステータスに更新
        job_manager.update_job_status(
            job_id,
            AnalysisStatus.COMPLETED,
            "分析が完了しました",
            progress=1.0,
            result=result
        )
        
        logger.info(f"分析完了: {job_id}")
        
    except Exception as e:
        logger.error(f"分析実行エラー: {str(e)}")
        job_manager.update_job_status(
            job_id,
            AnalysisStatus.FAILED,
            f"分析中にエラーが発生しました: {str(e)}",
            error_message=str(e)
        )

@router.get("/run/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    ジョブのステータスを取得
    
    Args:
        job_id: ジョブID
    
    Returns:
        JobStatus: ジョブステータス
    """
    try:
        job_status = job_manager.get_job_status(job_id)
        if not job_status:
            raise HTTPException(status_code=404, detail="ジョブが見つかりません")
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ジョブステータス取得エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ステータスの取得中にエラーが発生しました: {str(e)}"
        )

@router.post("/run/{job_id}/cancel")
async def cancel_job(job_id: str):
    """
    ジョブをキャンセル
    
    Args:
        job_id: ジョブID
    
    Returns:
        dict: キャンセル結果
    """
    try:
        success = job_manager.cancel_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="ジョブが見つかりません")
        
        return {"message": "ジョブがキャンセルされました", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ジョブキャンセルエラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ジョブのキャンセル中にエラーが発生しました: {str(e)}"
        )
