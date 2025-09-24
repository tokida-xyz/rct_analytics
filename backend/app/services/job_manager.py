"""
ジョブ管理サービス
分析ジョブの状態管理と結果保存を行う
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from threading import Lock

from app.models.schemas import JobStatus, AnalysisStatus, AnalysisResult
from app.core.config import settings

logger = logging.getLogger(__name__)

class JobManager:
    """ジョブ管理クラス"""
    
    def __init__(self):
        self.jobs: Dict[str, JobStatus] = {}
        self.results: Dict[str, AnalysisResult] = {}
        self.lock = Lock()
        
        # 結果ディレクトリの作成
        os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    
    def create_job(self, job_status: JobStatus) -> None:
        """ジョブを作成"""
        with self.lock:
            self.jobs[job_status.job_id] = job_status
            logger.info(f"ジョブ作成: {job_status.job_id}")
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """ジョブステータスを取得"""
        with self.lock:
            return self.jobs.get(job_id)
    
    def update_job_status(
        self, 
        job_id: str, 
        status: AnalysisStatus, 
        message: str = "",
        progress: float = 0.0,
        result: Optional[AnalysisResult] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """ジョブステータスを更新"""
        with self.lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            job.status = status
            job.message = message
            job.progress = progress
            job.updated_at = datetime.now()
            
            if result:
                self.results[job_id] = result
                job.completed_at = datetime.now()
            
            if error_message:
                job.message = f"エラー: {error_message}"
            
            logger.info(f"ジョブステータス更新: {job_id} -> {status}")
            return True
    
    def get_job_result(self, job_id: str) -> Optional[AnalysisResult]:
        """ジョブ結果を取得"""
        with self.lock:
            return self.results.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """ジョブをキャンセル"""
        with self.lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            if job.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                return False
            
            job.status = AnalysisStatus.FAILED
            job.message = "ユーザーによってキャンセルされました"
            job.updated_at = datetime.now()
            
            logger.info(f"ジョブキャンセル: {job_id}")
            return True
    
    def save_result(self, job_id: str, result: AnalysisResult) -> None:
        """分析結果をファイルに保存"""
        try:
            # 結果ディレクトリの作成
            result_dir = os.path.join(settings.RESULTS_DIR, job_id)
            os.makedirs(result_dir, exist_ok=True)
            os.makedirs(os.path.join(result_dir, "figures"), exist_ok=True)
            
            # 結果JSONの保存
            result_file = os.path.join(result_dir, "result.json")
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result.dict(), f, ensure_ascii=False, indent=2, default=str)
            
            # CSV結果の保存
            self._save_csv_result(job_id, result)
            
            # ログの保存
            self._save_analysis_log(job_id, result)
            
            logger.info(f"結果保存完了: {job_id}")
            
        except Exception as e:
            logger.error(f"結果保存エラー: {str(e)}")
            raise
    
    def _save_csv_result(self, job_id: str, result: AnalysisResult) -> None:
        """CSV結果を保存"""
        try:
            import pandas as pd
            
            # 結果データの準備
            csv_data = []
            for res in result.results:
                row = {
                    'moderator': res.moderator,
                    'outcome': res.outcome,
                    'n_used': res.n_used,
                    'median': res.median,
                    'mean': res.mean,
                    'std': res.std,
                    'beta_interaction': res.beta_interaction,
                    'p_interaction': res.p_interaction,
                    'q_interaction': res.q_interaction,
                    'partial_eta2': res.partial_eta2,
                    'simple_slope_low': res.simple_slope_low.slope,
                    'p_low': res.simple_slope_low.p_value,
                    'ci95_low_lower': res.simple_slope_low.ci_lower,
                    'ci95_low_upper': res.simple_slope_low.ci_upper,
                    'd_low': res.simple_slope_low.cohens_d,
                    'simple_slope_high': res.simple_slope_high.slope,
                    'p_high': res.simple_slope_high.p_value,
                    'ci95_high_lower': res.simple_slope_high.ci_lower,
                    'ci95_high_upper': res.simple_slope_high.ci_upper,
                    'd_high': res.simple_slope_high.cohens_d,
                    'r_squared': res.r_squared,
                    'adj_r_squared': res.adj_r_squared
                }
                csv_data.append(row)
            
            # CSVファイルの保存
            df = pd.DataFrame(csv_data)
            csv_path = os.path.join(settings.RESULTS_DIR, job_id, "interaction_summary.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
        except Exception as e:
            logger.error(f"CSV保存エラー: {str(e)}")
            raise
    
    def _save_analysis_log(self, job_id: str, result: AnalysisResult) -> None:
        """分析ログを保存"""
        try:
            log_path = os.path.join(settings.RESULTS_DIR, job_id, "analysis.log")
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"分析ログ - ジョブID: {job_id}\n")
                f.write(f"実行日時: {result.created_at}\n")
                f.write(f"完了日時: {result.completed_at}\n")
                f.write(f"ステータス: {result.status}\n\n")
                
                if result.logs:
                    f.write("詳細ログ:\n")
                    f.write(result.logs)
                
                if result.notes:
                    f.write("\n\n注記:\n")
                    for note in result.notes:
                        f.write(f"- {note}\n")
                
                if result.error_message:
                    f.write(f"\nエラーメッセージ:\n{result.error_message}\n")
        
        except Exception as e:
            logger.error(f"ログ保存エラー: {str(e)}")
            raise
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> None:
        """古いジョブをクリーンアップ"""
        try:
            current_time = datetime.now()
            jobs_to_remove = []
            
            with self.lock:
                for job_id, job in self.jobs.items():
                    age_hours = (current_time - job.created_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        jobs_to_remove.append(job_id)
                
                for job_id in jobs_to_remove:
                    del self.jobs[job_id]
                    if job_id in self.results:
                        del self.results[job_id]
            
            # ファイルのクリーンアップ
            for job_id in jobs_to_remove:
                result_dir = os.path.join(settings.RESULTS_DIR, job_id)
                if os.path.exists(result_dir):
                    import shutil
                    shutil.rmtree(result_dir)
            
            logger.info(f"古いジョブをクリーンアップ: {len(jobs_to_remove)}件")
            
        except Exception as e:
            logger.error(f"クリーンアップエラー: {str(e)}")
