# 株式投資アシスタント - データベースER図

## データベーススキーマ概要

株式投資アシスタントシステムのデータベース構造をMermaid形式で表現したER図です。

```mermaid
erDiagram
    %% 銘柄基本情報テーブル
    stocks {
        string stock_code PK "銘柄コード"
        string stock_name "銘柄名"
        string industry "業種"
        string market "市場"
        string description "説明"
        date listed_date "上場日"
        string website "ウェブサイト"
        timestamp created_at "作成日時"
        timestamp updated_at "更新日時"
    }

    %% ポートフォリオ保有テーブル
    portfolio_holdings {
        int holding_id PK "保有ID"
        string stock_code FK "銘柄コード"
        string holding_type "保有タイプ"
        string broker "証券会社"
        date purchase_date "購入日"
        decimal purchase_price "購入価格"
        int quantity "数量"
        decimal current_price "現在価格"
        text notes "備考"
        timestamp created_at "作成日時"
        timestamp updated_at "更新日時"
    }

    %% 取引計画テーブル
    trading_plans {
        int plan_id PK "計画ID"
        string stock_code FK "銘柄コード"
        date analysis_date "分析日"
        string analysis_type "分析タイプ"
        decimal allocation_percentage "配分率"
        text notes "備考"
        timestamp created_at "作成日時"
        timestamp updated_at "更新日時"
    }

    %% 買い判断テーブル
    buy_decisions {
        int buy_decision_id PK "買い判断ID"
        int plan_id FK "計画ID"
        text reason "理由"
        decimal target_price "目標価格"
        decimal min_buy_price "最低購入価格"
        decimal max_buy_price "最高購入価格"
        string timing "タイミング"
        decimal stop_loss "ストップロス"
        timestamp created_at "作成日時"
    }

    %% 売り判断テーブル
    sell_decisions {
        int sell_decision_id PK "売り判断ID"
        int plan_id FK "計画ID"
        decimal target_price "目標価格"
        decimal min_sell_price "最低売却価格"
        decimal max_sell_price "最高売却価格"
        string timing "タイミング"
        text reason "理由"
        timestamp created_at "作成日時"
    }

    %% リスク評価テーブル
    risk_assessments {
        int risk_id PK "リスクID"
        int plan_id FK "計画ID"
        string risk_type "リスクタイプ"
        string risk_level "リスクレベル"
        timestamp created_at "作成日時"
    }

    %% 監視ポイントテーブル（構造推測）
    monitoring_points {
        int monitoring_id PK "監視ID"
        string stock_code FK "銘柄コード"
        string indicator_type "指標タイプ"
        decimal threshold_value "閾値"
        string condition_type "条件タイプ"
        boolean is_active "有効フラグ"
        timestamp created_at "作成日時"
    }

    %% 取引条件テーブル（構造推測）
    trading_conditions {
        int condition_id PK "条件ID"
        string stock_code FK "銘柄コード"
        string condition_type "条件タイプ"
        string condition_value "条件値"
        string operator "演算子"
        boolean is_active "有効フラグ"
        timestamp created_at "作成日時"
    }

    %% リレーションシップ定義
    stocks ||--o{ portfolio_holdings : "保有"
    stocks ||--o{ trading_plans : "計画対象"
    trading_plans ||--|| buy_decisions : "買い判断"
    trading_plans ||--|| sell_decisions : "売り判断"
    trading_plans ||--o{ risk_assessments : "リスク評価"
    stocks ||--o{ monitoring_points : "監視対象"
    stocks ||--o{ trading_conditions : "取引条件"
```

## テーブル間の関係説明

### 主要エンティティ
1. **stocks（銘柄）**
   - 株式の基本情報を管理
   - 他のすべてのテーブルの親エンティティ

2. **portfolio_holdings（ポートフォリオ保有）**
   - 実際の保有状況を管理
   - stocksテーブルと1対多の関係

3. **trading_plans（取引計画）**
   - 投資計画の基本情報を管理
   - buy_decisions、sell_decisions、risk_assessmentsの親テーブル

### 判断・評価テーブル
4. **buy_decisions（買い判断）**
   - 買い判断の詳細条件を管理
   - trading_plansと1対1の関係

5. **sell_decisions（売り判断）**
   - 売り判断の詳細条件を管理
   - trading_plansと1対1の関係

6. **risk_assessments（リスク評価）**
   - リスク評価情報を管理
   - trading_plansと1対多の関係

### 監視・条件テーブル
7. **monitoring_points（監視ポイント）**
   - 価格や指標の監視ポイントを管理
   - stocksテーブルと1対多の関係

8. **trading_conditions（取引条件）**
   - 取引の条件設定を管理
   - stocksテーブルと1対多の関係

## 主キーと外部キーの関係

- **主キー（PK）**: 各テーブルの一意な識別子
- **外部キー（FK）**: 他のテーブルとの関連付け
  - `stock_code`: stocksテーブルを参照
  - `plan_id`: trading_plansテーブルを参照

## データフローの特徴

1. **銘柄中心の設計**: stocksテーブルを中心にすべての情報が関連付けられている
2. **計画ベースの判断**: trading_plansを基盤に買い/売り判断が行われる
3. **リスク管理の統合**: 取引計画ごとにリスク評価が関連付けられる
4. **監視機能の拡張**: リアルタイム監視のためのポイント管理

このデータモデルは、株式投資の意思決定プロセスを体系的に管理するための設計となっています。
