"""
データ処理サービス
ファイルの読み込み、型推定、前処理を行う
"""

import pandas as pd
import numpy as np
import os
import logging
from typing import List, Tuple, Dict, Any, Optional
from sklearn.preprocessing import StandardScaler
import re

from app.models.schemas import ColumnInfo, DataType

logger = logging.getLogger(__name__)

class DataProcessor:
    """データ処理クラス"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls']
    
    async def process_uploaded_file(
        self, 
        file_path: str, 
        preview_rows: int = 50
    ) -> Tuple[pd.DataFrame, List[ColumnInfo], List[Dict[str, Any]]]:
        """
        アップロードされたファイルを処理
        
        Args:
            file_path: ファイルパス
            preview_rows: プレビュー表示行数
        
        Returns:
            Tuple[pd.DataFrame, List[ColumnInfo], List[Dict]]: データフレーム、列情報、プレビューデータ
        """
        try:
            # ファイルの読み込み
            df = self._read_file(file_path)
            
            # 列情報の推定
            columns_info = self._analyze_columns(df)
            
            # プレビューデータの作成
            preview_data = self._create_preview_data(df, preview_rows)
            
            logger.info(f"ファイル処理完了: {file_path}, 行数: {len(df)}, 列数: {len(df.columns)}")
            return df, columns_info, preview_data
            
        except Exception as e:
            logger.error(f"ファイル処理エラー: {str(e)}")
            raise
    
    def _read_file(self, file_path: str) -> pd.DataFrame:
        """ファイルを読み込む"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.csv':
                # CSVファイルの読み込み（エンコーディング自動検出）
                encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("ファイルのエンコーディングを検出できませんでした")
                    
            elif file_extension in ['.xlsx', '.xls']:
                # Excelファイルの読み込み
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"サポートされていないファイル形式: {file_extension}")
            
            # 空の行・列を削除
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            return df
            
        except Exception as e:
            logger.error(f"ファイル読み込みエラー: {str(e)}")
            raise
    
    def _analyze_columns(self, df: pd.DataFrame) -> List[ColumnInfo]:
        """列の型と基本統計を分析"""
        columns_info = []
        
        for col in df.columns:
            # 基本統計
            unique_count = df[col].nunique()
            missing_count = df[col].isna().sum()
            missing_rate = missing_count / len(df)
            
            # サンプル値の取得（欠損値以外）
            sample_values = df[col].dropna().head(5).tolist()
            
            # データ型の推定
            data_type = self._infer_data_type(df[col])
            
            column_info = ColumnInfo(
                name=col,
                data_type=data_type,
                unique_count=unique_count,
                missing_count=missing_count,
                missing_rate=missing_rate,
                sample_values=sample_values
            )
            
            columns_info.append(column_info)
        
        return columns_info
    
    def _infer_data_type(self, series: pd.Series) -> DataType:
        """列のデータ型を推定"""
        # 欠損値を除外
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return DataType.TEXT
        
        # 数値型のチェック
        if pd.api.types.is_numeric_dtype(clean_series):
            # 整数かどうかチェック
            if clean_series.dtype in ['int64', 'int32', 'int16', 'int8']:
                # リッカート尺度の可能性をチェック
                unique_values = sorted(clean_series.unique())
                if len(unique_values) <= 7 and all(isinstance(x, (int, float)) and x > 0 for x in unique_values):
                    return DataType.ORDINAL
                else:
                    return DataType.NUMERIC
            else:
                return DataType.NUMERIC
        
        # カテゴリ型のチェック
        unique_count = clean_series.nunique()
        total_count = len(clean_series)
        
        if unique_count / total_count < 0.1 or unique_count <= 10:
            return DataType.CATEGORICAL
        
        # テキスト型
        return DataType.TEXT
    
    def _create_preview_data(self, df: pd.DataFrame, rows: int) -> List[Dict[str, Any]]:
        """プレビューデータを作成"""
        preview_df = df.head(rows)
        return preview_df.to_dict('records')
    
    def preprocess_data(
        self, 
        df: pd.DataFrame, 
        settings: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        データの前処理を実行
        
        Args:
            df: 元のデータフレーム
            settings: 処理設定
        
        Returns:
            pd.DataFrame: 前処理済みデータフレーム
        """
        try:
            processed_df = df.copy()
            
            # 平均中心化
            if settings.get('center_moderators', True):
                moderators = settings.get('moderators', [])
                for col in moderators:
                    if col in processed_df.columns:
                        processed_df[f"{col}_c"] = self._center_variable(processed_df[col])
            
            if settings.get('center_outcomes', False):
                outcomes = settings.get('outcomes', [])
                for col in outcomes:
                    if col in processed_df.columns:
                        processed_df[f"{col}_c"] = self._center_variable(processed_df[col])
            
            # 欠損値処理（リストワイズ除外）
            required_columns = (
                settings.get('moderators', []) + 
                settings.get('outcomes', []) + 
                [settings.get('intervention')]
            )
            required_columns = [col for col in required_columns if col in processed_df.columns]
            
            if required_columns:
                processed_df = processed_df.dropna(subset=required_columns)
            
            logger.info(f"データ前処理完了: {len(processed_df)}行")
            return processed_df
            
        except Exception as e:
            logger.error(f"データ前処理エラー: {str(e)}")
            raise
    
    def _center_variable(self, series: pd.Series) -> pd.Series:
        """変数の平均中心化"""
        return series - series.mean()
    
    def validate_intervention_variable(self, df: pd.DataFrame, intervention_col: str) -> bool:
        """介入変数の妥当性をチェック"""
        if intervention_col not in df.columns:
            return False
        
        unique_values = df[intervention_col].dropna().unique()
        return set(unique_values).issubset({0, 1, '0', '1'})
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """データの要約統計を取得"""
        summary = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_data': df.isnull().sum().sum(),
            'missing_rate': df.isnull().sum().sum() / (len(df) * len(df.columns)),
            'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
            'categorical_columns': len(df.select_dtypes(include=['object']).columns)
        }
        
        return summary
