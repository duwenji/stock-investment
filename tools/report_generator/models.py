#!/usr/bin/env python3
"""
データベースモデル定義
SQLAlchemy ORMを使用してテーブル構造を定義
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TechnicalIndicator(Base):
    """テクニカル指標テーブルモデル"""
    __tablename__ = 'technical_indicators'
    
    indicator_id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False)
    analysis_date = Column(Date, nullable=False)
    investment_style = Column(String(20), nullable=False)
    current_price = Column(Numeric(10, 2))
    sma_5 = Column(Numeric(10, 2))
    sma_10 = Column(Numeric(10, 2))
    sma_20 = Column(Numeric(10, 2))
    sma_50 = Column(Numeric(10, 2))
    rsi_14 = Column(Numeric(5, 2))
    macd_line = Column(Numeric(10, 4))
    macd_signal = Column(Numeric(10, 4))
    macd_histogram = Column(Numeric(10, 4))
    bb_upper = Column(Numeric(10, 2))
    bb_middle = Column(Numeric(10, 2))
    bb_lower = Column(Numeric(10, 2))
    stoch_k = Column(Numeric(5, 2))
    stoch_d = Column(Numeric(5, 2))
    volume_ratio = Column(Numeric(8, 4))
    price_change_1d = Column(Numeric(8, 4))
    price_change_5d = Column(Numeric(8, 4))
    price_change_20d = Column(Numeric(8, 4))
    volatility_20d = Column(Numeric(8, 4))
    confidence_score = Column(Numeric(3, 2))
    analysis_version = Column(String(20))
    created_at = Column(DateTime)

class InvestmentDecision(Base):
    """投資判断テーブルモデル"""
    __tablename__ = 'investment_decisions'
    
    decision_id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False)
    analysis_date = Column(Date, nullable=False)
    investment_style = Column(String(20), nullable=False)
    decision_type = Column(String(20))
    target_price = Column(Numeric(10, 2))
    stop_loss = Column(Numeric(10, 2))
    confidence_score = Column(Numeric(3, 2))
    rsi_signal = Column(String(10))
    macd_signal = Column(String(10))
    bb_signal = Column(String(10))
    stoch_signal = Column(String(10))
    overall_signal = Column(String(10))
    buy_count = Column(Integer)
    sell_count = Column(Integer)
    ai_reasoning = Column(Text)
    risk_assessment = Column(String(20))
    created_at = Column(DateTime)

class BacktestResult(Base):
    """バックテスト結果テーブルモデル"""
    __tablename__ = 'backtest_results'
    
    backtest_id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False)
    investment_style = Column(String(20), nullable=False)
    strategy_name = Column(String(50))
    start_date = Column(Date)
    end_date = Column(Date)
    total_return = Column(Numeric(8, 4))
    annual_return = Column(Numeric(8, 4))
    sharpe_ratio = Column(Numeric(6, 3))
    max_drawdown = Column(Numeric(8, 4))
    volatility = Column(Numeric(8, 4))
    win_rate = Column(Numeric(5, 3))
    profit_factor = Column(Numeric(6, 3))
    total_trades = Column(Integer)
    avg_trade_return = Column(Numeric(8, 4))
    benchmark_return = Column(Numeric(8, 4))
    created_at = Column(DateTime)
