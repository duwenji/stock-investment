# 株式投資アシスタント - 技術コンテキスト

## 技術スタック

### コア技術
- **プログラミング言語**: Python
- **データベース**: PostgreSQL
- **MCPサーバ**: postgres-mcp, yfinance-mcp, fetch-mcp
- **開発環境**: Visual Studio Code
- **バージョン管理**: Git

### 開発ツール
- **パッケージ管理**: uv (Python)
- **プロジェクト設定**: pyproject.toml
- **仮想環境**: uv venv
- **コード品質**: リンター、フォーマッター

## 開発環境設定

### 現在の環境
- **OS**: Windows 11
- **シェル**: CMD
- **作業ディレクトリ**: c:\Dev\stock-investment
- **Pythonバージョン**: .python-versionで指定

### プロジェクト構造
```
stock-investment/
├── data/                # データファイル
│   └── data_j.xls      # 株式データソース
├── tools/               # ユーティリティスクリプト
│   ├── sqlalchemy_import_stocks.py      # 株式データインポートスクリプト
│   └── import_stock_price_history.py    # 株価履歴取得スクリプト
├── memory-bank/         # プロジェクトドキュメント
├── pyproject.toml       # プロジェクト設定
├── uv.lock             # 依存関係ロック
├── .python-version     # Pythonバージョン
└── .gitignore         # Git除外設定
```

## MCPサーバ統合

### 接続済みMCPサーバ
1. **postgres-mcp**
   - PostgreSQLデータベース操作
   - テーブル作成、データCRUD操作
   - スキーマ管理、クエリ実行
   - 自動承認機能付き（安全な操作の自動実行）
   - Docker自動セットアップ対応

2. **yfinance-mcp**
   - 株価データの取得
   - 時系列データの収集
   - 株式情報の取得

3. **fetch-mcp**
   - Webサイトからのデータ取得
   - HTML/Markdown/JSON形式でのデータ収集
   - 外部情報源からの情報抽出

### MCPサーバ設定
詳細な設定情報は `mcp_server_config.md` を参照：
- タイムアウト設定: 60秒
- 自動承認対象操作の定義
- Docker環境変数設定
- ログレベルとデバッグ設定

### データベーススキーマ
既存のテーブル構造（postgres-mcp経由で確認）：
- `stocks` - 銘柄基本情報
- `portfolio_holdings` - ポートフォリオ保有
- `trading_plans` - 取引計画
- `buy_decisions` - 買い判断
- `sell_decisions` - 売り判断
- `risk_assessments` - リスク評価
- `monitoring_points` - 監視ポイント
- `trading_conditions` - 取引条件
- `stock_prices_history` - 株価履歴情報（新規作成）

## 依存関係管理

### 主要ライブラリ
- **データ分析**: pandas, numpy
- **可視化**: matplotlib, plotly
- **AI/ML**: scikit-learn, tensorflow (検討中)
- **Webスクレイピング**: requests, beautifulsoup4
- **データベース**: psycopg2, sqlalchemy

### 開発依存関係
- **テスト**: pytest
- **コード品質**: black, flake8, mypy
- **ドキュメント**: sphinx, mkdocs

## 開発ワークフロー

### セットアップ手順
1. Python環境のセットアップ（uvを使用）
2. 依存関係のインストール
3. データベース接続の設定
4. MCPサーバの起動と接続

### 開発プロセス
1. **要件定義**: memory-bankでのドキュメント化
2. **設計**: システムパターンの策定
3. **実装**: 機能ごとのモジュール開発
4. **テスト**: 単体テスト、統合テスト
5. **デプロイ**: 環境設定と実行

## 統合ポイント

### 外部API連携
- **株価データ**: yfinance API
- **金融情報**: 金融庁API、証券取引所API
- **ニュース**: 金融ニュースフィード

### データフロー統合
1. **データ収集**: MCPサーバ経由での外部データ取得
2. **データ処理**: Pythonでの分析と変換
3. **データ保存**: PostgreSQLへの永続化
4. **データ活用**: AI分析と可視化

## パフォーマンス考慮事項

### データ処理最適化
- バッチ処理による大量データの効率的な処理
- キャッシュ戦略による応答速度の向上
- 非同期処理による並列実行

### スケーリング戦略
- データベースのインデックス最適化
- クエリのパフォーマンスチューニング
- メモリ使用量の最適化
