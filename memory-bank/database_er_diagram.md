# 株式投資アシスタント - データベースER図

## データベーススキーマ概要

株式投資アシスタントシステムのデータベース構造をMermaid形式で表現したER図です。実際のデータベース構造に基づいて最新化され、外部キー制約が追加されています。

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
        date data_date "データ日"
        string industry_code_33 "33業種コード"
        string industry_code_17 "17業種コード"
        string scale_code "規模コード"
        string scale_category "規模区分"
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

    %% ポートフォリオパフォーマンステーブル
    portfolio_performance {
        int holding_id "保有ID"
        string stock_code "銘柄コード"
        string holding_type "保有タイプ"
        decimal total_cost "総コスト"
        decimal current_value "現在価値"
        decimal profit_loss "損益"
        decimal profit_loss_rate "損益率"
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

    %% 計画全体リスクテーブル
    plan_overall_risk {
        int plan_id "計画ID"
        string overall_risk "全体リスク"
    }

    %% 監視ポイントテーブル
    monitoring_points {
        int point_id PK "監視ID"
        int plan_id FK "計画ID"
        string point_category "ポイントカテゴリ"
        string point_description "ポイント説明"
        int priority "優先度"
        timestamp created_at "作成日時"
    }

    %% 取引条件テーブル
    trading_conditions {
        int condition_id PK "条件ID"
        int plan_id FK "計画ID"
        string condition_type "条件タイプ"
        string condition_category "条件カテゴリ"
        string operator "演算子"
        decimal min_value "最小値"
        decimal max_value "最大値"
        string value_text "テキスト値"
        int condition_order "条件順序"
        timestamp created_at "作成日時"
    }

    %% リレーションシップ定義（外部キー制約付き）
    stocks ||--o{ portfolio_holdings : "保有"
    stocks ||--o{ trading_plans : "計画対象"
    portfolio_holdings ||--|| portfolio_performance : "パフォーマンス"
    trading_plans ||--o{ buy_decisions : "買い判断"
    trading_plans ||--o{ sell_decisions : "売り判断"
    trading_plans ||--o{ risk_assessments : "リスク評価"
    trading_plans ||--|| plan_overall_risk : "全体リスク"
    trading_plans ||--o{ monitoring_points : "監視ポイント"
    trading_plans ||--o{ trading_conditions : "取引条件"
```

## テーブル間の関係説明

### 主要エンティティ
1. **stocks（銘柄）**
   - 株式の基本情報を管理
   - 業種コード、規模区分などの追加フィールドを含む
   - portfolio_holdings、trading_plansの親エンティティ

2. **portfolio_holdings（ポートフォリオ保有）**
   - 実際の保有状況を管理
   - portfolio_performanceと1対1の関係

3. **trading_plans（取引計画）**
   - 投資計画の基本情報を管理
   - buy_decisions、sell_decisions、risk_assessments、monitoring_points、trading_conditionsの親テーブル

### 判断・評価テーブル
4. **buy_decisions（買い判断）**
   - 買い判断の詳細条件を管理
   - trading_plansと1対多の関係

5. **sell_decisions（売り判断）**
   - 売り判断の詳細条件を管理
   - trading_plansと1対多の関係

6. **risk_assessments（リスク評価）**
   - リスク評価情報を管理
   - trading_plansと1対多の関係

7. **plan_overall_risk（計画全体リスク）**
   - 計画全体のリスク評価を管理
   - trading_plansと1対1の関係

### 監視・条件テーブル
8. **monitoring_points（監視ポイント）**
   - 価格や指標の監視ポイントを管理
   - trading_plansと1対多の関係

9. **trading_conditions（取引条件）**
   - 取引の条件設定を管理
   - trading_plansと1対多の関係

### パフォーマンステーブル
10. **portfolio_performance（ポートフォリオパフォーマンス）**
    - 保有銘柄のパフォーマンス情報を管理
    - portfolio_holdingsと1対1の関係

## 主キーと外部キーの関係

- **主キー（PK）**: 各テーブルの一意な識別子
- **外部キー（FK）**: 他のテーブルとの関連付け（データベース制約付き）
  - `stock_code`: stocksテーブルを参照
  - `plan_id`: trading_plansテーブルを参照
  - `holding_id`: portfolio_holdingsテーブルを参照

## 外部キー制約の詳細

以下の外部キー制約がデータベースに定義されています：

1. **portfolio_holdings → stocks**
   - `stock_code` → `stocks.stock_code`

2. **trading_plans → stocks**
   - `stock_code` → `stocks.stock_code`

3. **buy_decisions → trading_plans**
   - `plan_id` → `trading_plans.plan_id`

4. **sell_decisions → trading_plans**
   - `plan_id` → `trading_plans.plan_id`

5. **risk_assessments → trading_plans**
   - `plan_id` → `trading_plans.plan_id`

6. **monitoring_points → trading_plans**
   - `plan_id` → `trading_plans.plan_id`

7. **trading_conditions → trading_plans**
   - `plan_id` → `trading_plans.plan_id`

## データフローの特徴

1. **銘柄中心の設計**: stocksテーブルを中心に保有情報と計画情報が関連付けられている
2. **計画ベースの判断**: trading_plansを基盤に買い/売り判断、リスク評価、監視ポイント、取引条件が管理される
3. **リスク管理の統合**: 取引計画ごとに詳細リスク評価と全体リスク評価が関連付けられる
4. **監視機能の拡張**: 計画ベースの監視ポイント管理
5. **パフォーマンス追跡**: 保有銘柄のパフォーマンス情報を別途管理

## 重要な変更点

1. **stocksテーブルの拡張**:
   - `data_date`、`industry_code_33`、`industry_code_17`、`scale_code`、`scale_category`フィールドを追加

2. **新しいテーブルの追加**:
   - `portfolio_performance`: ポートフォリオパフォーマンス管理
   - `plan_overall_risk`: 計画全体のリスク評価

3. **外部キー制約の追加**:
   - 7つの外部キー制約をデータベースに追加
   - データ整合性と参照整合性を確保

4. **リレーションシップの正確化**:
   - 外部キー制約に基づいた正確な関係定義
   - trading_plansを中心とした1対多の関係構造

5. **フィールド名の正確化**:
   - monitoring_pointsの`point_id`、`point_category`、`point_description`など
   - trading_conditionsの`condition_category`、`min_value`、`max_value`など

このデータモデルは、株式投資の意思決定プロセスを体系的に管理するための設計となっています。実際のデータベース構造に基づいて正確に表現され、外部キー制約によってデータ整合性が確保されています。
