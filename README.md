# 株式データインポートスクリプト

## 概要
Excelファイル（data_j.xls）からPostgreSQLデータベースのstocksテーブルにデータをインポートするSQLAlchemyベースのスクリプトです。

## ファイル構成
- `tools/sqlalchemy_import_stocks.py` - メインのデータインポートスクリプト
- `data/data_j.xls` - 株式データソースファイル

## 使用方法

### 1. 環境設定
```bash
# 依存関係のインストール
uv add sqlalchemy pandas openpyxl
```

### 2. データベース接続設定
スクリプトはpostgres-mcpサーバから自動的に接続情報を取得します。
環境変数でカスタム接続情報を設定することも可能です：
```bash
# Windows (PowerShell)
$env:DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
```

### 3. 実行
```bash
# テストモード（データ処理のみ確認）
cd tools; python sqlalchemy_import_stocks.py --test

# 本番モード（データベースに投入）
cd tools; python sqlalchemy_import_stocks.py
```

## データ構造
Excelファイルのカラム：
- コード（銘柄コード）
- 銘柄名
- 市場・商品区分
- 33業種区分/コード
- 17業種区分/コード
- 規模コード/区分
- 日付（YYYYMMDD形式）

## 注意事項
- データベース接続には正しい認証情報が必要です
- 大量データ（4,412件）をバッチ処理で効率的に投入します
- 既存データは全て削除されます
