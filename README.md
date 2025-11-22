# 株式投資AIアシスタント

## 概要
生成AIを活用した株式投資支援システム。投資判断のサポート、ポートフォリオ管理、リスク評価をAIで支援します。

## プロジェクト構造

### コアシステム
- **AIアシスタント**: 生成AIによる投資判断支援と分析
- **データベース**: PostgreSQLを使用した投資データ管理
- **MCPサーバ統合**: 外部データソースとの連携

### ツールスクリプト
- `tools/import_stocks.py` - 株式基本データのインポートスクリプト
- `tools/import_stock_price_history.py` - 株価履歴情報の取得スクリプト

## 主要機能

### 1. 株式データ管理
- 銘柄基本情報の収集と保存
- 株価履歴データの自動取得
- 時系列データの分析と可視化

### 2. 投資判断支援
- AIによる買い/売り判断の提案
- テクニカル分析の自動化
- リスク評価の提供

### 3. ポートフォリオ管理
- 保有銘柄の追跡と損益計算
- 資産配分の最適化提案
- リアルタイムのパフォーマンス分析

## 使用方法

### 環境設定
```bash
# 依存関係のインストール
uv add sqlalchemy pandas openpyxl yfinance
```

### データベース接続設定
スクリプトはpostgres-mcpサーバから自動的に接続情報を取得します。
環境変数でカスタム接続情報を設定することも可能です：
```bash
# Windows (PowerShell)
$env:DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
```

### スクリプト実行

#### 株式基本データのインポート
```bash
# テストモード（データ処理のみ確認）
cd tools; python sqlalchemy_import_stocks.py --test

# 本番モード（データベースに投入）
cd tools; python sqlalchemy_import_stocks.py
```

#### 株価履歴情報の取得
```bash
# 保有銘柄の株価履歴を取得
cd tools; python import_stock_price_history.py
```

## スクリプト詳細

### sqlalchemy_import_stocks.py
Excelファイル（data_j.xls）からPostgreSQLデータベースのstocksテーブルにデータをインポートします。

**データ構造**:
- コード（銘柄コード）
- 銘柄名
- 市場・商品区分
- 33業種区分/コード
- 17業種区分/コード
- 規模コード/区分
- 日付（YYYYMMDD形式）

### import_stock_price_history.py
portfolio_holdingsテーブルの対象銘柄の株価履歴情報を取得し、stock_prices_historyテーブルに格納します。

**主な機能**:
- 保有銘柄一覧の自動取得
- yfinanceを使用した株価履歴の取得（1年分）
- データベースへの効率的な保存
- 最新株価でのポートフォリオ評価額の自動更新

## データベーススキーマ

既存のテーブル構造：
- `stocks` - 銘柄基本情報
- `portfolio_holdings` - ポートフォリオ保有
- `trading_plans` - 取引計画
- `buy_decisions` - 買い判断
- `sell_decisions` - 売り判断
- `risk_assessments` - リスク評価
- `monitoring_points` - 監視ポイント
- `trading_conditions` - 取引条件
- `stock_prices_history` - 株価履歴情報

## MCPサーバ統合

### 接続済みMCPサーバ
1. **postgres-mcp** - PostgreSQLデータベース操作
2. **yfinance-mcp** - 株価データの取得
3. **fetch-mcp** - Webサイトからのデータ取得

## 注意事項
- データベース接続には正しい認証情報が必要です
- 大量データをバッチ処理で効率的に投入します
- 株価履歴取得時は外部APIのレート制限に注意してください
- 既存データは上書きされる可能性があります

## 開発情報
詳細な技術情報と開発状況は `memory-bank/` ディレクトリを参照してください。
