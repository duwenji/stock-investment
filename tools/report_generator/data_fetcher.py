#!/usr/bin/env python3
"""
銘柄レポート生成用データ取得モジュール
portfolio_holdingsとtrading_plansから対象銘柄を取得し、関連データを収集
"""

import logging
import pandas as pd
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

class DataFetcher:
    """データ取得クラス"""
    
    def __init__(self):
        self.target_stocks = []
        self.engine = self._get_database_engine()
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _get_database_engine(self):
        """データベース接続エンジンを取得"""
        # 環境変数から接続情報を取得
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            # 既存のSQLAlchemyスクリプトと同じ接続情報を使用
            database_url = "postgresql://postgres:postgres@localhost:5432/mcp-postgres-db"
        
        logger.info(f"データベース接続URL: {database_url}")
        engine = create_engine(database_url)
        return engine
    
    def get_target_stock_codes(self) -> List[str]:
        """portfolio_holdingsとtrading_plansから対象銘柄コードを取得"""
        try:
            session = self.SessionLocal()
            
            query = text("""
            SELECT DISTINCT stock_code 
            FROM portfolio_holdings 
            WHERE stock_code IS NOT NULL 
            UNION 
            SELECT DISTINCT stock_code 
            FROM trading_plans 
            WHERE stock_code IS NOT NULL
            """)
            
            result = session.execute(query)
            stock_codes = [row[0] for row in result]
            
            logger.info(f"対象銘柄数: {len(stock_codes)}")
            logger.info(f"対象銘柄: {stock_codes}")
            self.target_stocks = stock_codes
            
            session.close()
            return stock_codes
                
        except Exception as e:
            logger.error(f"対象銘柄取得中にエラー: {e}")
            return []
    
    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict]:
        """銘柄の基本情報を取得"""
        try:
            session = self.SessionLocal()
            
            query = text("""
            SELECT stock_code, stock_name, industry, market, description, 
                   listed_date, website, industry_code_33, industry_code_17,
                   scale_code, scale_category
            FROM stocks 
            WHERE stock_code = :stock_code
            """)
            
            result = session.execute(query, {"stock_code": stock_code})
            row = result.fetchone()
            
            session.close()
            
            if row:
                return dict(row._mapping)
            else:
                logger.warning(f"銘柄 {stock_code} の基本情報が見つかりません")
                return None
                
        except Exception as e:
            logger.error(f"銘柄 {stock_code} の基本情報取得中にエラー: {e}")
            return None
    
    def get_stock_price_history(self, stock_code: str, days: int = 365) -> Optional[pd.DataFrame]:
        """銘柄の株価履歴を取得"""
        try:
            session = self.SessionLocal()
            
            query = text("""
            SELECT price_date, open_price, high_price, low_price, close_price, volume
            FROM stock_prices_history 
            WHERE stock_code = :stock_code
            ORDER BY price_date DESC
            LIMIT :days
            """)
            
            result = session.execute(query, {"stock_code": stock_code, "days": days})
            rows = result.fetchall()
            
            session.close()
            
            if rows:
                # データをDataFrameに変換
                df = pd.DataFrame([dict(row._mapping) for row in rows])
                df['price_date'] = pd.to_datetime(df['price_date'])
                df = df.sort_values('price_date').reset_index(drop=True)
                
                # 数値型に変換
                numeric_cols = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                logger.info(f"銘柄 {stock_code} の株価履歴取得完了: {len(df)}日分")
                return df
            else:
                logger.warning(f"銘柄 {stock_code} の株価履歴が見つかりません")
                return None
                
        except Exception as e:
            logger.error(f"銘柄 {stock_code} の株価履歴取得中にエラー: {e}")
            return None
    
    def get_portfolio_holdings_info(self, stock_code: str) -> List[Dict]:
        """銘柄のポートフォリオ保有情報を取得"""
        try:
            session = self.SessionLocal()
            
            query = text("""
            SELECT holding_id, holding_type, broker, purchase_date, 
                   purchase_price, quantity, current_price, notes
            FROM portfolio_holdings 
            WHERE stock_code = :stock_code
            """)
            
            result = session.execute(query, {"stock_code": stock_code})
            rows = result.fetchall()
            
            session.close()
            
            return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            logger.error(f"銘柄 {stock_code} のポートフォリオ情報取得中にエラー: {e}")
            return []
    
    def get_trading_plans_info(self, stock_code: str) -> List[Dict]:
        """銘柄の取引計画情報を取得"""
        try:
            session = self.SessionLocal()
            
            query = text("""
            SELECT plan_id, analysis_date, analysis_type, 
                   allocation_percentage, notes
            FROM trading_plans 
            WHERE stock_code = :stock_code
            """)
            
            result = session.execute(query, {"stock_code": stock_code})
            rows = result.fetchall()
            
            session.close()
            
            return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            logger.error(f"銘柄 {stock_code} の取引計画情報取得中にエラー: {e}")
            return []
    
    def get_all_stock_data(self, stock_code: str) -> Dict:
        """銘柄の全データを取得"""
        logger.info(f"銘柄 {stock_code} のデータ取得開始")
        
        basic_info = self.get_stock_basic_info(stock_code)
        price_history = self.get_stock_price_history(stock_code)
        portfolio_info = self.get_portfolio_holdings_info(stock_code)
        trading_plans = self.get_trading_plans_info(stock_code)
        
        return {
            "stock_code": stock_code,
            "basic_info": basic_info,
            "price_history": price_history,
            "portfolio_info": portfolio_info,
            "trading_plans": trading_plans
        }
