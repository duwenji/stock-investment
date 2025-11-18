# MCPサーバ設定

## 概要
このプロジェクトで使用されているMCP（Model Context Protocol）サーバの設定情報です。

## 設定内容

### yfinance MCPサーバ
```json
{
  "yfinance": {
    "timeout": 60,
    "type": "stdio",
    "command": "npx",
    "args": [
      "@onori/yfinance-mcp-server"
    ]
  }
}
```

**機能**:
- 株価データの取得
- 時系列データの収集
- 株式情報の取得

### postgres-mcpサーバ
```json
{
  "postgres-mcp": {
    "autoApprove": [
      "get_database_info",
      "get_tables",
      "read_entity",
      "create_table",
      "batch_create_entities",
      "execute_sql_query",
      "get_table_schema",
      "get_multiple_table_schemas"
    ],
    "disabled": false,
    "timeout": 60,
    "type": "stdio",
    "command": "uvx",
    "args": [
      "mcp-postgres-duwenji"
    ],
    "env": {
      "MCP_DOCKER_AUTO_SETUP": "true",
      "MCP_SLOW_QUERY_THRESHOLD_MS": "1000",
      "MCP_ENABLE_AUTO_EXPLAIN": "true",
      "MCP_DOCKER_IMAGE": "postgres:16",
      "MCP_DOCKER_CONTAINER_NAME": "mcp-postgres-auto",
      "MCP_DOCKER_PORT": "5432",
      "MCP_DOCKER_DATA_VOLUME": "mcp_postgres_data",
      "MCP_DOCKER_PASSWORD": "postgres",
      "MCP_DOCKER_DATABASE": "mcp-postgres-db",
      "MCP_DOCKER_USERNAME": "postgres",
      "MCP_DOCKER_MAX_WAIT_TIME": "30",
      "MCP_LOG_LEVEL": "DEBUG",
      "MCP_PROTOCOL_DEBUG": "true",
      "MCP_LOG_DIR": "Logs\\mcp-postgres"
    }
  }
}
```

**機能**:
- PostgreSQLデータベース操作
- テーブル作成、データCRUD操作
- スキーマ管理、クエリ実行
- 自動承認機能付き（安全な操作の自動実行）

**データベース接続情報**:
- **ホスト**: localhost
- **ポート**: 5432
- **データベース**: mcp-postgres-db
- **ユーザー名**: postgres
- **パスワード**: postgres

## 使用方法

### 1. データベース操作
```python
# postgres-mcpを使用したデータベース操作
from use_mcp_tool import use_mcp_tool

# テーブル一覧取得
result = use_mcp_tool(
    server_name="postgres-mcp",
    tool_name="get_tables"
)

# データ読み取り
result = use_mcp_tool(
    server_name="postgres-mcp",
    tool_name="read_entity",
    arguments={
        "table_name": "stocks",
        "limit": 10
    }
)
```

### 2. 株価データ取得
```python
# yfinance-mcpを使用した株価データ取得
result = use_mcp_tool(
    server_name="yfinance",
    tool_name="getStockHistory",
    arguments={
        "symbol": "AAPL",
        "period": "1mo",
        "interval": "1d"
    }
)
```

## 注意事項

1. **自動承認機能**: postgres-mcpサーバは特定の操作に対して自動承認が設定されています
2. **タイムアウト**: 各サーバのタイムアウトは60秒に設定されています
3. **ログレベル**: DEBUGモードで詳細なログが出力されます
4. **Docker自動セットアップ**: データベースが自動的にDockerコンテナで起動します

## トラブルシューティング

### 接続エラーが発生する場合
1. Dockerが起動していることを確認
2. ポート5432が使用されていないことを確認
3. ログファイルを確認: `C:\Dev\mcp\mcp-postgres\Logs\mcp-postgres`

### パフォーマンスが遅い場合
1. クエリの最適化を検討
2. インデックスの追加を検討
3. バッチ処理の活用

---

**最終更新**: 2025年11月18日
