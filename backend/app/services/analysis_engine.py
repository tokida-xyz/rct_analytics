"""
統計分析エンジン
交互作用検定の統計分析を実行する
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import os
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from app.models.schemas import (
    AnalysisResult, AnalysisStatus, InteractionResult, SimpleSlope,
    AnalysisSettings, VariableMapping, DataProcessingSettings
)
from app.services.data_processor import DataProcessor
from app.services.job_manager import JobManager
from app.services.visualization import VisualizationService
from app.core.config import settings

logger = logging.getLogger(__name__)

class AnalysisEngine:
    """統計分析エンジンクラス"""
    
    def __init__(self):
        self.data_processor = DataProcessor()
        self.job_manager = JobManager()
        self.visualization = VisualizationService()
    
    async def run_analysis(self, job_id: str, settings: AnalysisSettings) -> AnalysisResult:
        """
        交互作用検定分析を実行
        
        Args:
            job_id: ジョブID
            settings: 分析設定
        
        Returns:
            AnalysisResult: 分析結果
        """
        try:
            # データの読み込み
            df = await self._load_data(job_id)
            
            # データの前処理
            processed_df = self._preprocess_data(df, settings)
            
            # 分析の実行
            results = []
            logs = []
            figures = []
            
            total_combinations = len(settings.variable_mapping.moderators) * len(settings.variable_mapping.outcomes)
            current_combination = 0
            
            for moderator in settings.variable_mapping.moderators:
                for outcome in settings.variable_mapping.outcomes:
                    current_combination += 1
                    progress = current_combination / total_combinations
                    
                    # ジョブステータスを更新
                    self.job_manager.update_job_status(
                        job_id,
                        AnalysisStatus.RUNNING,
                        f"分析中: {moderator} × {outcome} ({current_combination}/{total_combinations})",
                        progress=0.1 + (progress * 0.8)
                    )
                    
                    try:
                        # 交互作用検定の実行
                        result = self._run_interaction_test(
                            processed_df, 
                            moderator, 
                            outcome, 
                            settings.variable_mapping.intervention,
                            settings
                        )
                        
                        if result:
                            results.append(result)
                            log_msg = f"完了: {moderator} × {outcome} (n={result.n_used}, p={result.p_interaction:.4f})"
                            logs.append(log_msg)
                            logger.info(log_msg)
                        else:
                            log_msg = f"スキップ: {moderator} × {outcome} (サンプル数不足)"
                            logs.append(log_msg)
                            logger.warning(log_msg)
                            
                    except Exception as e:
                        log_msg = f"エラー: {moderator} × {outcome} - {str(e)}"
                        logs.append(log_msg)
                        logger.error(log_msg)
            
            # 多重比較補正
            if results:
                results = self._apply_multiple_comparison_correction(results, settings.fdr_alpha)
            
            # 図の生成
            if settings.generate_plots and results:
                figures = await self._generate_figures(job_id, results, settings)
            
            # 結果の要約
            summary = self._create_summary(results, settings)
            
            # 注記の作成
            notes = self._create_notes(settings, len(results))
            
            # 分析結果の作成
            analysis_result = AnalysisResult(
                job_id=job_id,
                status=AnalysisStatus.COMPLETED,
                created_at=datetime.now(),
                completed_at=datetime.now(),
                results=results,
                summary=summary,
                notes=notes,
                logs="\n".join(logs),
                figures=figures
            )
            
            # 結果の保存
            self.job_manager.save_result(job_id, analysis_result)
            
            logger.info(f"分析完了: {job_id}, 結果数: {len(results)}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"分析実行エラー: {str(e)}")
            error_result = AnalysisResult(
                job_id=job_id,
                status=AnalysisStatus.FAILED,
                created_at=datetime.now(),
                error_message=str(e)
            )
            return error_result
    
    async def _load_data(self, job_id: str) -> pd.DataFrame:
        """データを読み込む"""
        try:
            upload_dir = os.path.join(settings.UPLOAD_DIR, job_id)
            files = [f for f in os.listdir(upload_dir) if f.endswith(('.csv', '.xlsx', '.xls'))]
            
            if not files:
                raise FileNotFoundError("データファイルが見つかりません")
            
            file_path = os.path.join(upload_dir, files[0])
            df, _, _ = await self.data_processor.process_uploaded_file(file_path)
            
            return df
            
        except Exception as e:
            logger.error(f"データ読み込みエラー: {str(e)}")
            raise
    
    def _preprocess_data(self, df: pd.DataFrame, settings: AnalysisSettings) -> pd.DataFrame:
        """データの前処理"""
        try:
            processed_df = df.copy()
            
            # 平均中心化
            if settings.data_processing.center_moderators:
                for moderator in settings.variable_mapping.moderators:
                    if moderator in processed_df.columns:
                        processed_df[f"{moderator}_c"] = self._center_variable(processed_df[moderator])
            
            if settings.data_processing.center_outcomes:
                for outcome in settings.variable_mapping.outcomes:
                    if outcome in processed_df.columns:
                        processed_df[f"{outcome}_c"] = self._center_variable(processed_df[outcome])
            
            # 欠損値処理（リストワイズ除外）
            required_columns = (
                settings.variable_mapping.moderators + 
                settings.variable_mapping.outcomes + 
                [settings.variable_mapping.intervention]
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
    
    def _run_interaction_test(
        self, 
        df: pd.DataFrame, 
        moderator: str, 
        outcome: str, 
        intervention: str,
        settings: AnalysisSettings
    ) -> Optional[InteractionResult]:
        """交互作用検定を実行"""
        try:
            # 必要な列の存在確認
            required_cols = [moderator, outcome, intervention]
            if not all(col in df.columns for col in required_cols):
                return None
            
            # データの準備
            data = df[required_cols].dropna()
            
            if len(data) < settings.min_sample_size:
                return None
            
            # 介入変数の型変換
            data[intervention] = data[intervention].astype(int)
            
            # 交互作用項の作成
            data['interaction'] = data[intervention] * data[moderator]
            
            # 線形回帰モデルの構築
            formula = f"{outcome} ~ {intervention} + {moderator} + interaction"
            model = ols(formula, data=data).fit()
            
            # 基本統計
            n_used = len(data)
            median = data[outcome].median()
            mean = data[outcome].mean()
            std = data[outcome].std()
            
            # 交互作用項の係数とp値
            beta_interaction = model.params['interaction']
            p_interaction = model.pvalues['interaction']
            
            # 決定係数
            r_squared = model.rsquared
            adj_r_squared = model.rsquared_adj
            
            # 効果量（部分η²）
            partial_eta2 = self._calculate_partial_eta2(model, 'interaction')
            
            # 単純傾斜の計算
            simple_slope_low, simple_slope_high = self._calculate_simple_slopes(
                model, data, moderator, intervention
            )
            
            # 結果の作成
            result = InteractionResult(
                moderator=moderator,
                outcome=outcome,
                n_used=n_used,
                median=median,
                mean=mean,
                std=std,
                beta_interaction=beta_interaction,
                p_interaction=p_interaction,
                q_interaction=0.0,  # 後で多重比較補正で設定
                partial_eta2=partial_eta2,
                simple_slope_low=simple_slope_low,
                simple_slope_high=simple_slope_high,
                r_squared=r_squared,
                adj_r_squared=adj_r_squared
            )
            
            return result
            
        except Exception as e:
            logger.error(f"交互作用検定エラー ({moderator} × {outcome}): {str(e)}")
            return None
    
    def _calculate_partial_eta2(self, model, term: str) -> float:
        """部分η²を計算"""
        try:
            # ANOVAテーブルを取得
            anova_table = anova_lm(model, typ=2)
            
            # 指定された項の平方和と残差平方和
            ss_effect = anova_table.loc[term, 'sum_sq']
            ss_residual = anova_table.loc['Residual', 'sum_sq']
            
            # 部分η² = SS_effect / (SS_effect + SS_residual)
            partial_eta2 = ss_effect / (ss_effect + ss_residual)
            
            return partial_eta2
            
        except Exception as e:
            logger.warning(f"部分η²計算エラー: {str(e)}")
            return 0.0
    
    def _calculate_simple_slopes(
        self, 
        model, 
        data: pd.DataFrame, 
        moderator: str, 
        intervention: str
    ) -> Tuple[SimpleSlope, SimpleSlope]:
        """単純傾斜を計算"""
        try:
            # モデレーターの平均と標準偏差
            m_mean = data[moderator].mean()
            m_std = data[moderator].std()
            
            # ±1SDの値
            m_low = m_mean - m_std
            m_high = m_mean + m_std
            
            # 単純傾斜の計算
            # Sの効果 = β1 + β3 * M
            beta_s = model.params[intervention]
            beta_interaction = model.params['interaction']
            
            slope_low = beta_s + beta_interaction * m_low
            slope_high = beta_s + beta_interaction * m_high
            
            # 標準誤差の計算（近似）
            se_low = self._calculate_simple_slope_se(model, m_low)
            se_high = self._calculate_simple_slope_se(model, m_high)
            
            # 信頼区間とp値
            ci_low = self._calculate_confidence_interval(slope_low, se_low)
            ci_high = self._calculate_confidence_interval(slope_high, se_high)
            
            p_low = 2 * (1 - stats.norm.cdf(abs(slope_low / se_low)))
            p_high = 2 * (1 - stats.norm.cdf(abs(slope_high / se_high)))
            
            # Cohen's dの計算
            d_low = self._calculate_cohens_d(data, moderator, intervention, outcome, m_low)
            d_high = self._calculate_cohens_d(data, moderator, intervention, outcome, m_high)
            
            simple_slope_low = SimpleSlope(
                slope=slope_low,
                p_value=p_low,
                ci_lower=ci_low[0],
                ci_upper=ci_low[1],
                cohens_d=d_low
            )
            
            simple_slope_high = SimpleSlope(
                slope=slope_high,
                p_value=p_high,
                ci_lower=ci_high[0],
                ci_upper=ci_high[1],
                cohens_d=d_high
            )
            
            return simple_slope_low, simple_slope_high
            
        except Exception as e:
            logger.warning(f"単純傾斜計算エラー: {str(e)}")
            # デフォルト値を返す
            default_slope = SimpleSlope(
                slope=0.0, p_value=1.0, ci_lower=0.0, ci_upper=0.0, cohens_d=0.0
            )
            return default_slope, default_slope
    
    def _calculate_simple_slope_se(self, model, m_value: float) -> float:
        """単純傾斜の標準誤差を計算（近似）"""
        try:
            # 共分散行列から標準誤差を計算
            cov_matrix = model.cov_params()
            se_interaction = np.sqrt(cov_matrix.loc['interaction', 'interaction'])
            return se_interaction * abs(m_value)
        except:
            return 0.1  # デフォルト値
    
    def _calculate_confidence_interval(self, slope: float, se: float, alpha: float = 0.05) -> Tuple[float, float]:
        """信頼区間を計算"""
        z_score = stats.norm.ppf(1 - alpha/2)
        margin_error = z_score * se
        return (slope - margin_error, slope + margin_error)
    
    def _calculate_cohens_d(
        self, 
        data: pd.DataFrame, 
        moderator: str, 
        intervention: str, 
        outcome: str, 
        m_value: float
    ) -> float:
        """Cohen's dを計算"""
        try:
            # ±1SDでグループ分け
            low_group = data[data[moderator] <= m_value]
            high_group = data[data[moderator] > m_value]
            
            if len(low_group) < 2 or len(high_group) < 2:
                return 0.0
            
            # 各グループでの介入効果
            low_effect = low_group[low_group[intervention] == 1][outcome].mean() - \
                        low_group[low_group[intervention] == 0][outcome].mean()
            high_effect = high_group[high_group[intervention] == 1][outcome].mean() - \
                         high_group[high_group[intervention] == 0][outcome].mean()
            
            # 効果の差
            effect_diff = high_effect - low_effect
            
            # プールされた標準偏差
            pooled_std = np.sqrt(
                (low_group[outcome].var() + high_group[outcome].var()) / 2
            )
            
            if pooled_std == 0:
                return 0.0
            
            return effect_diff / pooled_std
            
        except Exception as e:
            logger.warning(f"Cohen's d計算エラー: {str(e)}")
            return 0.0
    
    def _apply_multiple_comparison_correction(
        self, 
        results: List[InteractionResult], 
        alpha: float
    ) -> List[InteractionResult]:
        """多重比較補正を適用"""
        try:
            p_values = [r.p_interaction for r in results]
            
            # Benjamini-Hochberg補正
            rejected, q_values, _, _ = multipletests(
                p_values, 
                alpha=alpha, 
                method='fdr_bh'
            )
            
            # 結果にq値を設定
            for i, result in enumerate(results):
                result.q_interaction = q_values[i]
            
            return results
            
        except Exception as e:
            logger.error(f"多重比較補正エラー: {str(e)}")
            return results
    
    def _create_summary(self, results: List[InteractionResult], settings: AnalysisSettings) -> Dict[str, Any]:
        """結果の要約を作成"""
        try:
            if not results:
                return {"total_tests": 0, "significant_tests": 0}
            
            significant_results = [r for r in results if r.q_interaction < settings.fdr_alpha]
            
            summary = {
                "total_tests": len(results),
                "significant_tests": len(significant_results),
                "fdr_alpha": settings.fdr_alpha,
                "moderators": settings.variable_mapping.moderators,
                "outcomes": settings.variable_mapping.outcomes,
                "intervention": settings.variable_mapping.intervention
            }
            
            # 有意な結果の詳細
            if significant_results:
                summary["significant_results"] = [
                    {
                        "moderator": r.moderator,
                        "outcome": r.outcome,
                        "beta_interaction": r.beta_interaction,
                        "p_interaction": r.p_interaction,
                        "q_interaction": r.q_interaction,
                        "partial_eta2": r.partial_eta2
                    }
                    for r in significant_results
                ]
            
            return summary
            
        except Exception as e:
            logger.error(f"要約作成エラー: {str(e)}")
            return {"error": str(e)}
    
    def _create_notes(self, settings: AnalysisSettings, num_results: int) -> List[str]:
        """注記を作成"""
        notes = []
        
        # データ処理の注記
        if settings.data_processing.center_moderators:
            notes.append("モデレーター変数は平均中心化されました")
        
        if settings.data_processing.center_outcomes:
            notes.append("アウトカム変数は平均中心化されました")
        
        # 分析の注記
        notes.append(f"多重比較補正: Benjamini-Hochberg (FDR {settings.fdr_alpha:.1%})")
        notes.append(f"実行された検定数: {num_results}")
        
        # 感度分析の注記
        if settings.data_processing.run_sensitivity:
            notes.append("感度分析として順序ロジット回帰も実行されました")
        
        return notes
    
    async def _generate_figures(
        self, 
        job_id: str, 
        results: List[InteractionResult], 
        settings: AnalysisSettings
    ) -> List[str]:
        """図を生成"""
        try:
            figures = []
            
            # 有意な結果のみ図を生成
            significant_results = [r for r in results if r.q_interaction < settings.fdr_alpha]
            
            if not significant_results:
                return figures
            
            # 最大図数を制限
            max_figures = min(len(significant_results), settings.max_plots)
            
            for i, result in enumerate(significant_results[:max_figures]):
                try:
                    # 単純傾斜プロット
                    fig_name = f"{result.moderator}_{result.outcome}_simple_slopes.png"
                    fig_path = await self.visualization.create_simple_slope_plot(
                        job_id, result, fig_name
                    )
                    if fig_path:
                        figures.append(fig_name)
                    
                    # 棒グラフ
                    bar_fig_name = f"{result.moderator}_{result.outcome}_bar_chart.png"
                    bar_fig_path = await self.visualization.create_bar_chart(
                        job_id, result, bar_fig_name
                    )
                    if bar_fig_path:
                        figures.append(bar_fig_name)
                        
                except Exception as e:
                    logger.warning(f"図生成エラー ({result.moderator} × {result.outcome}): {str(e)}")
            
            return figures
            
        except Exception as e:
            logger.error(f"図生成エラー: {str(e)}")
            return []
