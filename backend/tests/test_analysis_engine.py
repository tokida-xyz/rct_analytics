"""
統計分析エンジンのテスト
"""

import pytest
import pandas as pd
import numpy as np
from app.services.analysis_engine import AnalysisEngine
from app.models.schemas import AnalysisSettings, VariableMapping, DataProcessingSettings

class TestAnalysisEngine:
    """統計分析エンジンのテストクラス"""
    
    def setup_method(self):
        """テストのセットアップ"""
        self.engine = AnalysisEngine()
        
        # テスト用データの作成
        np.random.seed(123)
        n = 200
        
        # モデレーター変数
        B = np.random.normal(0, 1, n)
        C = np.random.normal(0, 1, n)
        D = np.random.normal(0, 1, n)
        E = np.random.normal(0, 1, n)
        F = np.random.normal(0, 1, n)
        
        # 介入フラグ
        S = np.random.randint(0, 2, n)
        
        # アウトカム変数（交互作用を含む）
        G = 0.5 * S + 0.3 * B + 0.2 * (S * B) + np.random.normal(0, 0.5, n)
        H = 0.4 * S + 0.2 * C + 0.1 * (S * C) + np.random.normal(0, 0.5, n)
        I = 0.3 * S + 0.1 * D + 0.05 * (S * D) + np.random.normal(0, 0.5, n)
        
        self.test_data = pd.DataFrame({
            'B': B, 'C': C, 'D': D, 'E': E, 'F': F,
            'G': G, 'H': H, 'I': I,
            'S': S
        })
        
        # 分析設定
        self.settings = AnalysisSettings(
            variable_mapping=VariableMapping(
                moderators=['B', 'C', 'D'],
                outcomes=['G', 'H', 'I'],
                intervention='S'
            ),
            data_processing=DataProcessingSettings(
                center_outcomes=False,
                center_moderators=True,
                ordinal_outcomes=[],
                run_sensitivity=False,
                seed=123
            ),
            fdr_alpha=0.05,
            min_sample_size=30,
            generate_plots=False,
            max_plots=10
        )
    
    def test_preprocess_data(self):
        """データ前処理のテスト"""
        processed_df = self.engine._preprocess_data(self.test_data, self.settings)
        
        # 中心化された列が存在するかチェック
        for moderator in self.settings.variable_mapping.moderators:
            assert f"{moderator}_c" in processed_df.columns
        
        # データが欠損値なしで処理されているかチェック
        required_columns = (
            self.settings.variable_mapping.moderators + 
            self.settings.variable_mapping.outcomes + 
            [self.settings.variable_mapping.intervention]
        )
        for col in required_columns:
            assert not processed_df[col].isna().any()
    
    def test_run_interaction_test(self):
        """交互作用検定のテスト"""
        processed_df = self.engine._preprocess_data(self.test_data, self.settings)
        
        result = self.engine._run_interaction_test(
            processed_df,
            'B',
            'G',
            'S',
            self.settings
        )
        
        assert result is not None
        assert result.moderator == 'B'
        assert result.outcome == 'G'
        assert result.n_used > 0
        assert 0 <= result.p_interaction <= 1
        assert 0 <= result.partial_eta2 <= 1
        assert result.simple_slope_low is not None
        assert result.simple_slope_high is not None
    
    def test_calculate_partial_eta2(self):
        """部分η²計算のテスト"""
        from statsmodels.formula.api import ols
        
        # 簡単なモデルでテスト
        data = self.test_data[['G', 'S', 'B']].dropna()
        data['interaction'] = data['S'] * data['B']
        
        model = ols('G ~ S + B + interaction', data=data).fit()
        partial_eta2 = self.engine._calculate_partial_eta2(model, 'interaction')
        
        assert 0 <= partial_eta2 <= 1
    
    def test_calculate_simple_slopes(self):
        """単純傾斜計算のテスト"""
        from statsmodels.formula.api import ols
        
        data = self.test_data[['G', 'S', 'B']].dropna()
        data['interaction'] = data['S'] * data['B']
        
        model = ols('G ~ S + B + interaction', data=data).fit()
        
        slope_low, slope_high = self.engine._calculate_simple_slopes(
            model, data, 'B', 'S'
        )
        
        assert slope_low is not None
        assert slope_high is not None
        assert slope_low.slope is not None
        assert slope_high.slope is not None
        assert 0 <= slope_low.p_value <= 1
        assert 0 <= slope_high.p_value <= 1
    
    def test_apply_multiple_comparison_correction(self):
        """多重比較補正のテスト"""
        from app.models.schemas import InteractionResult, SimpleSlope
        
        # モック結果を作成
        results = []
        for i in range(5):
            result = InteractionResult(
                moderator=f'M{i}',
                outcome=f'O{i}',
                n_used=100,
                median=3.0,
                mean=3.0,
                std=1.0,
                beta_interaction=0.1,
                p_interaction=0.01 + i * 0.01,  # 異なるp値
                q_interaction=0.0,
                partial_eta2=0.1,
                simple_slope_low=SimpleSlope(0.1, 0.05, 0.0, 0.2, 0.1),
                simple_slope_high=SimpleSlope(0.1, 0.05, 0.0, 0.2, 0.1),
                r_squared=0.1,
                adj_r_squared=0.1
            )
            results.append(result)
        
        corrected_results = self.engine._apply_multiple_comparison_correction(
            results, 0.05
        )
        
        assert len(corrected_results) == len(results)
        for result in corrected_results:
            assert result.q_interaction >= 0
            assert result.q_interaction <= 1
    
    def test_create_summary(self):
        """結果要約のテスト"""
        from app.models.schemas import InteractionResult, SimpleSlope
        
        # モック結果を作成
        results = []
        for i in range(3):
            result = InteractionResult(
                moderator=f'M{i}',
                outcome=f'O{i}',
                n_used=100,
                median=3.0,
                mean=3.0,
                std=1.0,
                beta_interaction=0.1,
                p_interaction=0.01,
                q_interaction=0.01 if i < 2 else 0.1,  # 最初の2つを有意にする
                partial_eta2=0.1,
                simple_slope_low=SimpleSlope(0.1, 0.05, 0.0, 0.2, 0.1),
                simple_slope_high=SimpleSlope(0.1, 0.05, 0.0, 0.2, 0.1),
                r_squared=0.1,
                adj_r_squared=0.1
            )
            results.append(result)
        
        summary = self.engine._create_summary(results, self.settings)
        
        assert summary['total_tests'] == 3
        assert summary['significant_tests'] == 2
        assert 'fdr_alpha' in summary
        assert 'moderators' in summary
        assert 'outcomes' in summary
        assert 'intervention' in summary
    
    def test_create_notes(self):
        """注記作成のテスト"""
        notes = self.engine._create_notes(self.settings, 5)
        
        assert len(notes) > 0
        assert any('多重比較補正' in note for note in notes)
        assert any('実行された検定数' in note for note in notes)
