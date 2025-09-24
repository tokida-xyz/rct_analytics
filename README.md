# 交互作用検定 Webアプリ

rawデータ（CSV/XLSX）を読み込み、交互作用（モデレーション）検定と要約表・図の自動生成を行うWebアプリケーションです。

## 機能概要

- **データアップロード**: CSV/XLSXファイルのドラッグ&ドロップ対応
- **自動型推定**: 列のデータ型を自動検出（numeric/categorical/ordinal）
- **変数設定**: モデレーター、アウトカム、介入フラグの柔軟な設定
- **交互作用検定**: B〜F（モデレーター）× G〜R（アウトカム）× 介入Sの一括検定
- **多重比較補正**: Benjamini-Hochberg（FDR 5%）対応
- **可視化**: 単純傾斜プロット、棒グラフの自動生成
- **結果出力**: CSV、PNG、ログファイルのダウンロード

## 技術スタック

### バックエンド
- Python 3.11+
- FastAPI
- pandas, numpy, statsmodels, scikit-learn
- matplotlib, openpyxl

### フロントエンド
- React 18
- Vite
- TypeScript
- shadcn/ui

## プロジェクト構造

```
interaction-analysis-app/
├── backend/                 # FastAPIバックエンド
│   ├── app/
│   │   ├── api/            # APIエンドポイント
│   │   ├── core/           # 設定・認証
│   │   ├── models/         # データモデル
│   │   ├── services/       # ビジネスロジック
│   │   └── utils/          # ユーティリティ
│   ├── requirements.txt
│   └── main.py
├── frontend/                # Reactフロントエンド
│   ├── src/
│   │   ├── components/     # UIコンポーネント
│   │   ├── pages/          # ページコンポーネント
│   │   ├── services/       # API通信
│   │   ├── types/          # TypeScript型定義
│   │   └── utils/          # ユーティリティ
│   ├── package.json
│   └── vite.config.ts
├── tests/                   # テストファイル
├── docs/                    # ドキュメント
└── docker-compose.yml       # 開発環境用
```

## セットアップ

### 前提条件
- Python 3.11+
- Node.js 18+
- Docker（オプション）

### 開発環境のセットアップ

1. リポジトリのクローン
```bash
git clone <repository-url>
cd interaction-analysis-app
```

2. バックエンドのセットアップ
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. フロントエンドのセットアップ
```bash
cd frontend
npm install
```

4. 開発サーバーの起動
```bash
# バックエンド（ポート8000）
cd backend
uvicorn app.main:app --reload

# フロントエンド（ポート3000）
cd frontend
npm run dev
```

## 使用方法

1. ブラウザで `http://localhost:3000` にアクセス
2. CSV/XLSXファイルをアップロード
3. 列の型と役割を確認・設定
4. 分析設定を調整
5. 解析を実行
6. 結果を確認・ダウンロード

## API仕様

### エンドポイント

- `POST /api/upload`: ファイルアップロード
- `POST /api/run`: 解析実行
- `GET /api/result/{job_id}`: 結果取得
- `GET /api/download/{job_id}/csv`: CSVダウンロード
- `GET /api/download/{job_id}/logs`: ログダウンロード
- `GET /api/download/{job_id}/figs/{name}.png`: 図ダウンロード

### データ形式

詳細なAPI仕様は `/docs` エンドポイントでSwagger UIを確認できます。

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告を歓迎します。

## 更新履歴

- v1.0.0: 初期リリース
