#!/usr/bin/env python3
"""
portfolio_holdingsテーブルの保有銘柄の最新株価を更新するスクリプト（SQLAlchemy版）
"""

import sys
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import create_engine, Column, String, Integer, Numeric, Date, Text, TIMESTAMP
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import Session

# MCPツールのインポート
try:
    from use_mcp_tool import use_mcp_tool
except ImportError:
    # 開発環境でのフォールバック
    def use_mcp_tool(server_name, tool_name, arguments):
        logger.warning(f"MCPツールが利用できません: {server_name}.{tool_name}")
        return None

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('portfolio_price_update.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# SQLAlchemy モデル定義
Base = declarative_base()

class PortfolioHolding(Base):
    """portfolio_holdingsテーブルのORMモデル"""
    __tablename__ = 'portfolio_holdings'
    
    holding_id = Column(Integer, primary_key=True)
    stock_code = Column(String(10))
    holding_type = Column(String(20))
    broker = Column(String(50))
    purchase_date = Column(Date)
    purchase_price = Column(Numeric(10, 2))
    quantity = Column(Integer)
    current_price = Column(Numeric(10, 2))
    notes = Column(Text)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

def get_database_engine():
    """データベース接続エンジンを取得"""
    # 環境変数から接続情報を取得
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # postgres-mcpから取得した正しい接続情報を使用
        database_url = "postgresql://postgres:postgres@localhost:5432/mcp-postgres-db"
    
    logger.info(f"データベース接続URL: {database_url}")
    engine = create_engine(database_url)
    return engine

def get_unique_stock_codes(session: Session) -> List[str]:
    """portfolio_holdingsからユニークな銘柄コードを取得"""
    try:
        # SQLAlchemyを使用して銘柄コードを取得
        stock_codes = session.query(PortfolioHolding.stock_code).distinct().all()
        unique_codes = [code[0] for code in stock_codes]
        
        logger.info(f"ユニーク銘柄数: {len(unique_codes)}")
        logger.info(f"処理対象銘柄: {unique_codes}")
        return unique_codes
        
    except Exception as e:
        logger.error(f"銘柄コード取得中にエラー: {e}")
        return []

def convert_to_yfinance_symbol(stock_code: str) -> str:
    """日本株の証券コードをyfinance用のシンボルに変換"""
    # 日本株の場合、".T"を追加
    return f"{stock_code}.T"

def get_stock_price(stock_code: str) -> Optional[float]:
    """yfinance-mcpを使用して株価を取得"""
    try:
        yfinance_symbol = convert_to_yfinance_symbol(stock_code)
        logger.info(f"株価取得中: {stock_code} -> {yfinance_symbol}")
        
        # MCPツールを使用して株価を取得
        result = use_mcp_tool(
            server_name="yfinance",
            tool_name="getStockHistory",
            arguments={
                "symbol": yfinance_symbol,
                "period": "1d",
                "interval": "1d"
            }
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            # 最新の株価データを取得
            latest_data = result[-1]
            close_price = latest_data.get("close")
            if close_price:
                logger.info(f"{stock_code}の株価: {close_price}")
                return float(close_price)
        
        logger.warning(f"{stock_code}の株価取得に失敗")
        return None
        
    except Exception as e:
        logger.error(f"{stock_code}の株価取得中にエラー: {e}")
        return None

def update_portfolio_prices(session: Session, stock_prices: Dict[str, float]) -> Dict[str, int]:
    """portfolio_holdingsテーブルの株価を更新"""
    try:
        update_results = {"success": 0, "failed": 0}
        
        for stock_code, price in stock_prices.items():
            try:
                # SQLAlchemyを使用して更新
                updated_count = session.query(PortfolioHolding).filter(
                    PortfolioHolding.stock_code == stock_code
                ).update({
                    "current_price": price,
                    "updated_at": datetime.now()
                })
                
                if updated_count > 0:
                    update_results["success"] += updated_count
                    logger.info(f"{stock_code}の株価を{price}に更新しました ({updated_count}件)")
                else:
                    update_results["failed"] += 1
                    logger.error(f"{stock_code}の株価更新に失敗")
                    
            except Exception as e:
                update_results["failed"] += 1
                logger.error(f"{stock_code}の更新中にエラー: {e}")
        
        # 変更をコミット
        session.commit()
        return update_results
        
    except Exception as e:
        logger.error(f"ポートフォリオ更新中にエラー: {e}")
        session.rollback()
        return {"success": 0, "failed": 0}

def main():
    """メイン処理"""
    logger.info("=== ポートフォリオ株価更新開始 (SQLAlchemy版) ===")
    start_time = datetime.now()
    
    try:
        # データベース接続
        engine = get_database_engine()
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # 1. 保有銘柄一覧の取得
        stock_codes = get_unique_stock_codes(session)
        if not stock_codes:
            logger.error("保有銘柄がありません")
            return
        
        # 2. 株価の取得
        stock_prices = {}
        failed_stocks = []
        
        for stock_code in stock_codes:
            price = get_stock_price(stock_code)
            if price is not None:
                stock_prices[stock_code] = price
            else:
                failed_stocks.append(stock_code)
        
        logger.info(f"株価取得完了: 成功 {len(stock_prices)}銘柄, 失敗 {len(failed_stocks)}銘柄")
        if failed_stocks:
            logger.warning(f"株価取得失敗銘柄: {failed_stocks}")
        
        # 3. データベース更新
        if stock_prices:
            update_results = update_portfolio_prices(session, stock_prices)
            logger.info(f"データベース更新結果: 成功 {update_results['success']}件, 失敗 {update_results['failed']}件")
        else:
            logger.warning("更新する株価データがありません")
        
        # 4. 実行結果のサマリー
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info("=== ポートフォリオ株価更新完了 ===")
        logger.info(f"実行時間: {execution_time:.2f}秒")
        logger.info(f"総銘柄数: {len(stock_codes)}")
        logger.info(f"株価取得成功: {len(stock_prices)}")
        logger.info(f"株価取得失敗: {len(failed_stocks)}")
        
        if failed_stocks:
            logger.info(f"失敗銘柄詳細: {failed_stocks}")
            
    except Exception as e:
        logger.error(f"メイン処理中にエラー: {e}")
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main()
