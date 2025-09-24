"""
APIエンドポイントのテスト
"""

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
import os
import tempfile

class TestAPI:
    """APIエンドポイントのテストクラス"""
    
    def setup_method(self):
        """テストのセットアップ"""
        self.client = TestClient(app)
        
        # テスト用CSVファイルの作成
        np.random.seed(123)
        n = 100
        
        # テストデータの作成
        data = {
            'B': np.random.normal(0, 1, n),
            'C': np.random.normal(0, 1, n),
            'D': np.random.normal(0, 1, n),
            'E': np.random.normal(0, 1, n),
            'F': np.random.normal(0, 1, n),
            'G': np.random.normal(0, 1, n),
            'H': np.random.randint(1, 6, n),
            'I': np.random.randint(1, 6, n),
            'J': np.random.randint(1, 6, n),
            'K': np.random.randint(1, 6, n),
            'L': np.random.randint(1, 6, n),
            'M': np.random.randint(1, 6, n),
            'N': np.random.randint(1, 6, n),
            'O': np.random.randint(1, 6, n),
            'P': np.random.randint(1, 6, n),
            'Q': np.random.randint(1, 6, n),
            'R': np.random.randint(1, 6, n),
            'S': np.random.randint(0, 2, n),
        }
        
        self.test_df = pd.DataFrame(data)
        
        # 一時ファイルの作成
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.test_df.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()
    
    def teardown_method(self):
        """テストのクリーンアップ"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_root_endpoint(self):
        """ルートエンドポイントのテスト"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health_check(self):
        """ヘルスチェックのテスト"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_upload_file(self):
        """ファイルアップロードのテスト"""
        with open(self.temp_file.name, 'rb') as f:
            response = self.client.post(
                "/api/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "filename" in data
        assert "columns" in data
        assert "preview_data" in data
        
        # ジョブIDを保存
        self.job_id = data["job_id"]
    
    def test_upload_invalid_file(self):
        """無効なファイルアップロードのテスト"""
        # 存在しないファイル
        response = self.client.post(
            "/api/upload",
            files={"file": ("nonexistent.txt", b"dummy content", "text/plain")}
        )
        assert response.status_code == 400
    
    def test_get_data_preview(self):
        """データプレビューのテスト"""
        # まずファイルをアップロード
        with open(self.temp_file.name, 'rb') as f:
            upload_response = self.client.post(
                "/api/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        job_id = upload_response.json()["job_id"]
        
        # プレビューを取得
        response = self.client.get(f"/api/upload/{job_id}/preview")
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "preview_data" in data
        assert "total_rows" in data
        assert "columns" in data
    
    def test_run_analysis(self):
        """分析実行のテスト"""
        # まずファイルをアップロード
        with open(self.temp_file.name, 'rb') as f:
            upload_response = self.client.post(
                "/api/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        job_id = upload_response.json()["job_id"]
        
        # 分析リクエスト
        analysis_request = {
            "job_id": job_id,
            "settings": {
                "variable_mapping": {
                    "moderators": ["B", "C", "D"],
                    "outcomes": ["G", "H", "I"],
                    "intervention": "S"
                },
                "data_processing": {
                    "center_outcomes": False,
                    "center_moderators": True,
                    "ordinal_outcomes": [],
                    "run_sensitivity": False,
                    "seed": 123
                },
                "fdr_alpha": 0.05,
                "min_sample_size": 30,
                "generate_plots": False,
                "max_plots": 10
            }
        }
        
        response = self.client.post("/api/run", json=analysis_request)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert "message" in data
    
    def test_get_job_status(self):
        """ジョブステータスのテスト"""
        # まずファイルをアップロード
        with open(self.temp_file.name, 'rb') as f:
            upload_response = self.client.post(
                "/api/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        job_id = upload_response.json()["job_id"]
        
        # 分析を開始
        analysis_request = {
            "job_id": job_id,
            "settings": {
                "variable_mapping": {
                    "moderators": ["B"],
                    "outcomes": ["G"],
                    "intervention": "S"
                },
                "data_processing": {
                    "center_outcomes": False,
                    "center_moderators": True,
                    "ordinal_outcomes": [],
                    "run_sensitivity": False,
                    "seed": 123
                },
                "fdr_alpha": 0.05,
                "min_sample_size": 30,
                "generate_plots": False,
                "max_plots": 10
            }
        }
        
        self.client.post("/api/run", json=analysis_request)
        
        # ステータスを取得
        response = self.client.get(f"/api/run/{job_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert "progress" in data
    
    def test_cancel_job(self):
        """ジョブキャンセルのテスト"""
        # まずファイルをアップロード
        with open(self.temp_file.name, 'rb') as f:
            upload_response = self.client.post(
                "/api/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        job_id = upload_response.json()["job_id"]
        
        # 分析を開始
        analysis_request = {
            "job_id": job_id,
            "settings": {
                "variable_mapping": {
                    "moderators": ["B"],
                    "outcomes": ["G"],
                    "intervention": "S"
                },
                "data_processing": {
                    "center_outcomes": False,
                    "center_moderators": True,
                    "ordinal_outcomes": [],
                    "run_sensitivity": False,
                    "seed": 123
                },
                "fdr_alpha": 0.05,
                "min_sample_size": 30,
                "generate_plots": False,
                "max_plots": 10
            }
        }
        
        self.client.post("/api/run", json=analysis_request)
        
        # ジョブをキャンセル
        response = self.client.post(f"/api/run/{job_id}/cancel")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "job_id" in data
