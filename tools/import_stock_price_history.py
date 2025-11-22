#!/usr/bin/env python3
"""
portfolio_holdingsとtrading_plansの対象銘柄の株価履歴情報を取得し、stock_prices_historyテーブルに格納するスクリプト
"""

import sys
import os
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, String, Integer, Numeric, Date, Text, TIMESTAMP, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import Session
import yfinance as yf
import pandas as pd

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('stock_price_history_import.log', encoding='utf-8')
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

class TradingPlan(Base):
    """trading_plansテーブルのORMモデル"""
    __tablename__ = 'trading_plans'
    
    plan_id = Column(Integer, primary_key=True)
    stock_code = Column(String(10))
    analysis_date = Column(Date)
    analysis_type = Column(String(100))
    allocation_percentage = Column(Numeric(5, 2))
    notes = Column(Text)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

class StockPriceHistory(Base):
    """stock_prices_historyテーブルのORMモデル"""
    __tablename__ = 'stock_prices_history'
    
    price_id = Column(Integer, primary_key=True)
    stock_code = Column(String(10))
    price_date = Column(Date)
    open_price = Column(Numeric(10, 2))
    high_price = Column(Numeric(10, 2))
    low_price = Column(Numeric(10, 2))
    close_price = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    created_at = Column(TIMESTAMP)

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
    """portfolio_holdingsとtrading_plansからユニークな銘柄コードを取得"""
    try:
        # portfolio_holdingsから銘柄コードを取得
        portfolio_codes = session.query(PortfolioHolding.stock_code).distinct().all()
        portfolio_codes = [code[0] for code in portfolio_codes]
        
        # trading_plansから銘柄コードを取得
        trading_codes = session.query(TradingPlan.stock_code).distinct().all()
        trading_codes = [code[0] for code in trading_codes]
        
        # 両方のリストを結合して重複を除去
        all_codes = list(set(portfolio_codes + trading_codes))
        
        logger.info(f"ユニーク銘柄数: {len(all_codes)}")
        logger.info(f"portfolio_holdings銘柄: {portfolio_codes}")
        logger.info(f"trading_plans銘柄: {trading_codes}")
        logger.info(f"処理対象銘柄: {all_codes}")
        return all_codes
        
    except Exception as e:
        logger.error(f"銘柄コード取得中にエラー: {e}")
        return []

def convert_to_yfinance_symbol(stock_code: str) -> str:
    """日本株の証券コードをyfinance用のシンボルに変換"""
    # 日本株の場合、".T"を追加
    return f"{stock_code}.T"

def get_stock_price_history(stock_code: str, period: str = "max") -> Optional[pd.DataFrame]:
    """yfinanceを使用して株価履歴を取得（最大可能期間）"""
    try:
        yfinance_symbol = convert_to_yfinance_symbol(stock_code)
        logger.info(f"株価履歴取得中: {stock_code} -> {yfinance_symbol} (期間: {period})")
        
        # yfinanceで株価履歴を取得（最大可能期間）
        ticker = yf.Ticker(yfinance_symbol)
        hist_data = ticker.history(period=period)
        
        if hist_data.empty:
            logger.warning(f"{stock_code}の株価履歴データがありません")
            return None
        
        logger.info(f"{stock_code}の株価履歴取得完了: {len(hist_data)}日分（{hist_data.index[0].date()} 〜 {hist_data.index[-1].date()}）")
        return hist_data
        
    except Exception as e:
        logger.error(f"{stock_code}の株価履歴取得中にエラー: {e}")
        return None

def save_price_history(session: Session, stock_code: str, hist_data: pd.DataFrame) -> int:
    """株価履歴データをデータベースに保存"""
    try:
        saved_count = 0
        
        # 最新の日付と終値を取得
        latest_date = hist_data.index[-1].date()
        latest_close_price = float(hist_data.iloc[-1]['Close']) if pd.notna(hist_data.iloc[-1]['Close']) else None
        logger.info(f"{stock_code}の最新日付: {latest_date}, 最新終値: {latest_close_price}")
        
        for date, row in hist_data.iterrows():
            try:
                # 既存データの確認（重複防止）
                existing = session.query(StockPriceHistory).filter(
                    StockPriceHistory.stock_code == stock_code,
                    StockPriceHistory.price_date == date.date()
                ).first()
                
                if existing:
                    continue  # 既存データはスキップ
                
                # 新しいレコードを作成
                price_record = StockPriceHistory(
                    stock_code=stock_code,
                    price_date=date.date(),
                    open_price=float(row['Open']) if pd.notna(row['Open']) else None,
                    high_price=float(row['High']) if pd.notna(row['High']) else None,
                    low_price=float(row['Low']) if pd.notna(row['Low']) else None,
                    close_price=float(row['Close']) if pd.notna(row['Close']) else None,
                    volume=int(row['Volume']) if pd.notna(row['Volume']) else None,
                    created_at=datetime.now()
                )
                
                session.add(price_record)
                saved_count += 1
                
            except Exception as e:
                logger.error(f"{stock_code} {date.date()}のデータ保存中にエラー: {e}")
                continue
        
        # 最新の株価でportfolio_holdingsのcurrent_priceを更新
        if latest_close_price is not None:
            updated_count = session.query(PortfolioHolding).filter(
                PortfolioHolding.stock_code == stock_code
            ).update({
                "current_price": latest_close_price,
                "updated_at": datetime.now()
            })
            if updated_count > 0:
                logger.info(f"{stock_code}のcurrent_priceを{latest_close_price}に更新しました ({updated_count}件)")
            else:
                logger.warning(f"{stock_code}のcurrent_price更新対象が見つかりませんでした")
        
        # バッチコミット
        session.commit()
        return saved_count
        
    except Exception as e:
        logger.error(f"{stock_code}の株価履歴保存中にエラー: {e}")
        session.rollback()
        return 0

def main():
    """メイン処理"""
    logger.info("=== 株価履歴情報インポート開始 ===")
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
        
        # 2. 各銘柄の株価履歴を取得して保存
        total_saved = 0
        failed_stocks = []
        
        for stock_code in stock_codes:
            try:
                # 株価履歴の取得（最大可能期間）
                hist_data = get_stock_price_history(stock_code, period="max")
                
                if hist_data is not None:
                    # データベースに保存
                    saved_count = save_price_history(session, stock_code, hist_data)
                    total_saved += saved_count
                    logger.info(f"{stock_code}: {saved_count}件の株価履歴を保存しました")
                else:
                    failed_stocks.append(stock_code)
                    logger.warning(f"{stock_code}: 株価履歴の取得に失敗")
                    
            except Exception as e:
                failed_stocks.append(stock_code)
                logger.error(f"{stock_code}の処理中にエラー: {e}")
        
        # 3. 実行結果のサマリー
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info("=== 株価履歴情報インポート完了 ===")
        logger.info(f"実行時間: {execution_time:.2f}秒")
        logger.info(f"総銘柄数: {len(stock_codes)}")
        logger.info(f"株価履歴保存成功: {len(stock_codes) - len(failed_stocks)}銘柄")
        logger.info(f"株価履歴保存失敗: {len(failed_stocks)}銘柄")
        logger.info(f"総保存件数: {total_saved}件")
        
        if failed_stocks:
            logger.info(f"失敗銘柄詳細: {failed_stocks}")
            
    except Exception as e:
        logger.error(f"メイン処理中にエラー: {e}")
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main()
