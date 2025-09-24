"""
Pydanticスキーマ定義
APIのリクエスト・レスポンスの型定義
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import uuid
from datetime import datetime

class DataType(str, Enum):
    """データ型の列挙型"""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    ORDINAL = "ordinal"
    TEXT = "text"

class AnalysisStatus(str, Enum):
    """分析ステータスの列挙型"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ColumnInfo(BaseModel):
    """列情報のスキーマ"""
    name: str
    data_type: DataType
    unique_count: int
    missing_count: int
    missing_rate: float
    sample_values: List[Any] = Field(default_factory=list)
    
class UploadResponse(BaseModel):
    """ファイルアップロードレスポンス"""
    job_id: str
    filename: str
    columns: List[ColumnInfo]
    preview_data: List[Dict[str, Any]]
    message: str

class VariableMapping(BaseModel):
    """変数マッピング設定"""
    moderators: List[str] = Field(..., description="モデレーター変数名のリスト")
    outcomes: List[str] = Field(..., description="アウトカム変数名のリスト")
    intervention: str = Field(..., description="介入フラグ変数名")
    
    @validator('moderators', 'outcomes')
    def validate_non_empty(cls, v):
        if not v:
            raise ValueError('リストは空にできません')
        return v

class DataProcessingSettings(BaseModel):
    """データ処理設定"""
    center_outcomes: bool = Field(default=False, description="アウトカムの平均中心化")
    center_moderators: bool = Field(default=True, description="モデレーターの平均中心化")
    ordinal_outcomes: List[str] = Field(default_factory=list, description="順序尺度として扱うアウトカム")
    run_sensitivity: bool = Field(default=False, description="感度分析の実行")
    seed: int = Field(default=123, description="乱数シード")

class AnalysisSettings(BaseModel):
    """分析設定"""
    variable_mapping: VariableMapping
    data_processing: DataProcessingSettings
    fdr_alpha: float = Field(default=0.05, ge=0.001, le=0.5, description="FDR補正のα値")
    min_sample_size: int = Field(default=30, ge=10, description="最小サンプル数")
    generate_plots: bool = Field(default=True, description="図の生成")
    max_plots: int = Field(default=20, ge=1, le=100, description="最大図生成数")

class AnalysisRequest(BaseModel):
    """分析実行リクエスト"""
    job_id: str
    settings: AnalysisSettings

class SimpleSlope(BaseModel):
    """単純傾斜の結果"""
    slope: float
    p_value: float
    ci_lower: float
    ci_upper: float
    cohens_d: float

class InteractionResult(BaseModel):
    """交互作用検定結果"""
    moderator: str
    outcome: str
    n_used: int
    median: float
    mean: float
    std: float
    beta_interaction: float
    p_interaction: float
    q_interaction: float
    partial_eta2: float
    simple_slope_low: SimpleSlope
    simple_slope_high: SimpleSlope
    r_squared: float
    adj_r_squared: float

class AnalysisResult(BaseModel):
    """分析結果"""
    job_id: str
    status: AnalysisStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: List[InteractionResult] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)
    logs: str = ""
    figures: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None

class JobStatus(BaseModel):
    """ジョブステータス"""
    job_id: str
    status: AnalysisStatus
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    message: str = ""
    created_at: datetime
    updated_at: datetime

class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    error: str
    detail: Optional[str] = None
    job_id: Optional[str] = None
