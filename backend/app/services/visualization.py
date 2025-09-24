"""
可視化サービス
分析結果の図表生成を行う
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import numpy as np
import pandas as pd
import os
import logging
from typing import Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from app.models.schemas import InteractionResult
from app.core.config import settings

logger = logging.getLogger(__name__)

# 日本語フォントの設定
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

class VisualizationService:
    """可視化サービスクラス"""
    
    def __init__(self):
        self.figure_size = (10, 6)
        self.dpi = 300
        self.style = 'whitegrid'
        
        # スタイルの設定
        sns.set_style(self.style)
        sns.set_palette("husl")
    
    async def create_simple_slope_plot(
        self, 
        job_id: str, 
        result: InteractionResult, 
        filename: str
    ) -> Optional[str]:
        """
        単純傾斜プロットを作成
        
        Args:
            job_id: ジョブID
            result: 交互作用結果
            filename: ファイル名
        
        Returns:
            Optional[str]: 保存されたファイルパス
        """
        try:
            fig, ax = plt.subplots(figsize=self.figure_size)
            
            # データポイントの準備
            x_values = np.array([-1, 1])  # -1SD, +1SD
            y_values = np.array([
                result.simple_slope_low.slope,
                result.simple_slope_high.slope
            ])
            
            # 信頼区間
            ci_lower = np.array([
                result.simple_slope_low.ci_lower,
                result.simple_slope_high.ci_lower
            ])
            ci_upper = np.array([
                result.simple_slope_low.ci_upper,
                result.simple_slope_high.ci_upper
            ])
            
            # プロット
            ax.plot(x_values, y_values, 'o-', linewidth=2, markersize=8, 
                   label=f'{result.moderator} × {result.outcome}')
            
            # 信頼区間のプロット
            ax.fill_between(x_values, ci_lower, ci_upper, alpha=0.3)
            
            # 軸の設定
            ax.set_xlabel(f'{result.moderator} (標準化値)')
            ax.set_ylabel(f'{result.outcome} への介入効果')
            ax.set_title(f'単純傾斜プロット: {result.moderator} × {result.outcome}\n'
                        f'交互作用: β={result.beta_interaction:.3f}, '
                        f'p={result.p_interaction:.3f}, '
                        f'q={result.q_interaction:.3f}')
            
            # グリッドと凡例
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # レイアウトの調整
            plt.tight_layout()
            
            # ファイルの保存
            fig_path = await self._save_figure(job_id, fig, filename)
            
            plt.close(fig)
            return fig_path
            
        except Exception as e:
            logger.error(f"単純傾斜プロット生成エラー: {str(e)}")
            return None
    
    async def create_bar_chart(
        self, 
        job_id: str, 
        result: InteractionResult, 
        filename: str
    ) -> Optional[str]:
        """
        棒グラフを作成
        
        Args:
            job_id: ジョブID
            result: 交互作用結果
            filename: ファイル名
        
        Returns:
            Optional[str]: 保存されたファイルパス
        """
        try:
            fig, ax = plt.subplots(figsize=self.figure_size)
            
            # データの準備
            categories = ['Low (-1SD)', 'High (+1SD)']
            effects = [
                result.simple_slope_low.slope,
                result.simple_slope_high.slope
            ]
            errors = [
                (result.simple_slope_low.ci_upper - result.simple_slope_low.ci_lower) / 2,
                (result.simple_slope_high.ci_upper - result.simple_slope_high.ci_lower) / 2
            ]
            
            # 棒グラフのプロット
            bars = ax.bar(categories, effects, yerr=errors, capsize=5, 
                         alpha=0.7, color=['skyblue', 'lightcoral'])
            
            # 有意性の表示
            for i, (effect, error) in enumerate(zip(effects, errors)):
                p_value = result.simple_slope_low.p_value if i == 0 else result.simple_slope_high.p_value
                significance = '***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'
                
                ax.text(i, effect + error + 0.01, significance, 
                       ha='center', va='bottom', fontweight='bold')
            
            # 軸の設定
            ax.set_ylabel(f'{result.outcome} への介入効果')
            ax.set_title(f'介入効果の比較: {result.moderator} × {result.outcome}\n'
                        f'交互作用: β={result.beta_interaction:.3f}, '
                        f'p={result.p_interaction:.3f}')
            
            # グリッド
            ax.grid(True, alpha=0.3, axis='y')
            
            # レイアウトの調整
            plt.tight_layout()
            
            # ファイルの保存
            fig_path = await self._save_figure(job_id, fig, filename)
            
            plt.close(fig)
            return fig_path
            
        except Exception as e:
            logger.error(f"棒グラフ生成エラー: {str(e)}")
            return None
    
    async def create_summary_plot(
        self, 
        job_id: str, 
        results: list, 
        filename: str = "summary_plot.png"
    ) -> Optional[str]:
        """
        結果の要約プロットを作成
        
        Args:
            job_id: ジョブID
            results: 結果リスト
            filename: ファイル名
        
        Returns:
            Optional[str]: 保存されたファイルパス
        """
        try:
            if not results:
                return None
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 左側: p値の分布
            p_values = [r.p_interaction for r in results]
            q_values = [r.q_interaction for r in results]
            
            ax1.hist(p_values, bins=20, alpha=0.7, label='Raw p-values', color='skyblue')
            ax1.hist(q_values, bins=20, alpha=0.7, label='FDR-corrected q-values', color='lightcoral')
            ax1.axvline(0.05, color='red', linestyle='--', label='α = 0.05')
            ax1.set_xlabel('p-value')
            ax1.set_ylabel('Frequency')
            ax1.set_title('p値の分布')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 右側: 効果量の分布
            effect_sizes = [r.partial_eta2 for r in results]
            
            ax2.hist(effect_sizes, bins=20, alpha=0.7, color='lightgreen')
            ax2.set_xlabel('Partial η²')
            ax2.set_ylabel('Frequency')
            ax2.set_title('効果量（部分η²）の分布')
            ax2.grid(True, alpha=0.3)
            
            # レイアウトの調整
            plt.tight_layout()
            
            # ファイルの保存
            fig_path = await self._save_figure(job_id, fig, filename)
            
            plt.close(fig)
            return fig_path
            
        except Exception as e:
            logger.error(f"要約プロット生成エラー: {str(e)}")
            return None
    
    async def create_heatmap(
        self, 
        job_id: str, 
        results: list, 
        filename: str = "interaction_heatmap.png"
    ) -> Optional[str]:
        """
        交互作用のヒートマップを作成
        
        Args:
            job_id: ジョブID
            results: 結果リスト
            filename: ファイル名
        
        Returns:
            Optional[str]: 保存されたファイルパス
        """
        try:
            if not results:
                return None
            
            # データの準備
            moderators = list(set(r.moderator for r in results))
            outcomes = list(set(r.outcome for r in results))
            
            # マトリックスの作成
            p_matrix = np.full((len(moderators), len(outcomes)), np.nan)
            q_matrix = np.full((len(moderators), len(outcomes)), np.nan)
            
            for result in results:
                m_idx = moderators.index(result.moderator)
                o_idx = outcomes.index(result.outcome)
                p_matrix[m_idx, o_idx] = result.p_interaction
                q_matrix[m_idx, o_idx] = result.q_interaction
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 左側: p値のヒートマップ
            sns.heatmap(p_matrix, 
                     xticklabels=outcomes, 
                     yticklabels=moderators,
                     annot=True, 
                     fmt='.3f',
                     cmap='RdYlBu_r',
                     ax=ax1)
            ax1.set_title('Raw p-values')
            ax1.set_xlabel('Outcomes')
            ax1.set_ylabel('Moderators')
            
            # 右側: q値のヒートマップ
            sns.heatmap(q_matrix, 
                     xticklabels=outcomes, 
                     yticklabels=moderators,
                     annot=True, 
                     fmt='.3f',
                     cmap='RdYlBu_r',
                     ax=ax2)
            ax2.set_title('FDR-corrected q-values')
            ax2.set_xlabel('Outcomes')
            ax2.set_ylabel('Moderators')
            
            # レイアウトの調整
            plt.tight_layout()
            
            # ファイルの保存
            fig_path = await self._save_figure(job_id, fig, filename)
            
            plt.close(fig)
            return fig_path
            
        except Exception as e:
            logger.error(f"ヒートマップ生成エラー: {str(e)}")
            return None
    
    async def _save_figure(self, job_id: str, fig, filename: str) -> Optional[str]:
        """図を保存"""
        try:
            # 保存ディレクトリの作成
            save_dir = os.path.join(settings.RESULTS_DIR, job_id, "figures")
            os.makedirs(save_dir, exist_ok=True)
            
            # ファイルパス
            file_path = os.path.join(save_dir, filename)
            
            # 図の保存
            fig.savefig(file_path, dpi=self.dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            
            logger.info(f"図を保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"図保存エラー: {str(e)}")
            return None
