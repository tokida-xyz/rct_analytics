"""
データ処理サービスのテスト
"""

import pytest
import pandas as pd
import numpy as np
from app.services.data_processor import DataProcessor
from app.models.schemas import DataType

class TestDataProcessor:
    """データ処理サービスのテストクラス"""
    
    def setup_method(self):
        """テストのセットアップ"""
        self.processor = DataProcessor()
        
        # テスト用データの作成
        np.random.seed(123)
        self.test_data = pd.DataFrame({
            'A': np.random.normal(0, 1, 100),
            'B': np.random.normal(0, 1, 100),
            'C': np.random.normal(0, 1, 100),
            'D': np.random.normal(0, 1, 100),
            'E': np.random.normal(0, 1, 100),
            'F': np.random.normal(0, 1, 100),
            'G': np.random.normal(0, 1, 100),
            'H': np.random.randint(1, 6, 100),  # リッカート尺度
            'I': np.random.randint(1, 6, 100),  # リッカート尺度
            'J': np.random.randint(1, 6, 100),  # リッカート尺度
            'K': np.random.randint(1, 6, 100),  # リッカート尺度
            'L': np.random.randint(1, 6, 100),  # リッカート尺度
            'M': np.random.randint(1, 6, 100),  # リッカート尺度
            'N': np.random.randint(1, 6, 100),  # リッカート尺度
            'O': np.random.randint(1, 6, 100),  # リッカート尺度
            'P': np.random.randint(1, 6, 100),  # リッカート尺度
            'Q': np.random.randint(1, 6, 100),  # リッカート尺度
            'R': np.random.randint(1, 6, 100),  # リッカート尺度
            'S': np.random.randint(0, 2, 100),  # 介入フラグ
        })
    
    def test_infer_data_type_numeric(self):
        """数値型の推定テスト"""
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        data_type = self.processor._infer_data_type(series)
        assert data_type == DataType.NUMERIC
    
    def test_infer_data_type_ordinal(self):
        """順序尺度の推定テスト"""
        series = pd.Series([1, 2, 3, 4, 5])
        data_type = self.processor._infer_data_type(series)
        assert data_type == DataType.ORDINAL
    
    def test_infer_data_type_categorical(self):
        """カテゴリ型の推定テスト"""
        series = pd.Series(['A', 'B', 'C', 'A', 'B'])
        data_type = self.processor._infer_data_type(series)
        assert data_type == DataType.CATEGORICAL
    
    def test_analyze_columns(self):
        """列分析のテスト"""
        columns_info = self.processor._analyze_columns(self.test_data)
        
        assert len(columns_info) == len(self.test_data.columns)
        
        for col_info in columns_info:
            assert col_info.name in self.test_data.columns
            assert col_info.unique_count > 0
            assert 0 <= col_info.missing_rate <= 1
    
    def test_center_variable(self):
        """変数の平均中心化テスト"""
        series = pd.Series([1, 2, 3, 4, 5])
        centered = self.processor._center_variable(series)
        
        assert abs(centered.mean()) < 1e-10  # 平均が0に近い
        assert len(centered) == len(series)
    
    def test_validate_intervention_variable(self):
        """介入変数の妥当性チェックテスト"""
        # 有効な介入変数
        valid_data = pd.DataFrame({'S': [0, 1, 0, 1, 0]})
        assert self.processor.validate_intervention_variable(valid_data, 'S') == True
        
        # 無効な介入変数
        invalid_data = pd.DataFrame({'S': [0, 1, 2, 0, 1]})
        assert self.processor.validate_intervention_variable(invalid_data, 'S') == False
    
    def test_get_data_summary(self):
        """データ要約のテスト"""
        summary = self.processor.get_data_summary(self.test_data)
        
        assert summary['total_rows'] == 100
        assert summary['total_columns'] == 21
        assert summary['missing_data'] >= 0
        assert 0 <= summary['missing_rate'] <= 1
    
    def test_preprocess_data(self):
        """データ前処理のテスト"""
        settings = {
            'moderators': ['B', 'C', 'D', 'E', 'F'],
            'outcomes': ['G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R'],
            'intervention': 'S',
            'center_moderators': True,
            'center_outcomes': False
        }
        
        processed_df = self.processor.preprocess_data(self.test_data, settings)
        
        # 中心化された列が存在するかチェック
        for moderator in settings['moderators']:
            if settings['center_moderators']:
                assert f"{moderator}_c" in processed_df.columns
        
        # 元の列も存在するかチェック
        for col in settings['moderators'] + settings['outcomes'] + [settings['intervention']]:
            assert col in processed_df.columns
