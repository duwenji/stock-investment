#!/usr/bin/env python3
"""
データベース操作モジュール
SQLAlchemyを使用して分析結果をデータベースに保存
"""

import logging
from typing import Dict, List
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from models import TechnicalIndicator, InvestmentDecision, BacktestResult, Base

logger = logging.getLogger(__name__)

class AnalysisDataManager:
    """分析データ管理クラス"""
    
    def __init__(self, database_url: str = None):
        """
        Args:
            database_url: データベース接続URL（Noneの場合は既存設定を使用）
        """
        self.investment_styles = {
            'short_term': '短期投資',
            'long_term': '長期投資'
        }
        
        # データベース接続の設定
        if database_url is None:
            # 既存のデータベース接続設定を使用
            database_url = "postgresql://postgres:password@localhost:5432/stock_investment"
        
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # テーブルが存在することを確認
        try:
            Base.metadata.create_all(self.engine)
            logger.info("データベース接続を初期化しました")
        except Exception as e:
            logger.warning(f"データベース接続初期化中に警告: {e}")
    
    def save_technical_indicators(self, stock_code: str, indicators: Dict, 
                                investment_style: str, analysis_date: date = None) -> bool:
        """テクニカル指標をデータベースに保存"""
        session = self.Session()
        try:
            if analysis_date is None:
                analysis_date = date.today()
            
            # 投資スタイルの検証
            if investment_style not in self.investment_styles:
                logger.warning(f"無効な投資スタイル: {investment_style}")
                return False
            
            # 信頼度スコアの計算
            confidence_score = self._calculate_confidence_score(indicators)
            
            # 重複チェック
            existing = session.query(TechnicalIndicator).filter(
                TechnicalIndicator.stock_code == stock_code,
                TechnicalIndicator.analysis_date == analysis_date,
                TechnicalIndicator.investment_style == investment_style
            ).first()
            
            if existing:
                logger.info(f"銘柄 {stock_code} のテクニカル指標は既に存在します（スタイル: {investment_style}）")
                return True
            
            # 新しいレコードを作成
            indicator = TechnicalIndicator(
                stock_code=stock_code,
                analysis_date=analysis_date,
                investment_style=investment_style,
                current_price=indicators.get('current_price'),
                sma_5=indicators.get('sma_5'),
                sma_10=indicators.get('sma_10'),
                sma_20=indicators.get('sma_20'),
                sma_50=indicators.get('sma_50'),
                rsi_14=indicators.get('rsi_14'),
                macd_line=indicators.get('macd_line'),
                macd_signal=indicators.get('macd_signal'),
                macd_histogram=indicators.get('macd_histogram'),
                bb_upper=indicators.get('bb_upper'),
                bb_middle=indicators.get('bb_middle'),
                bb_lower=indicators.get('bb_lower'),
                stoch_k=indicators.get('stoch_k'),
                stoch_d=indicators.get('stoch_d'),
                volume_ratio=indicators.get('volume_ratio'),
                price_change_1d=indicators.get('price_change_1d'),
                price_change_5d=indicators.get('price_change_5d'),
                price_change_20d=indicators.get('price_change_20d'),
                volatility_20d=indicators.get('volatility_20d'),
                confidence_score=confidence_score,
                analysis_version='v1.0',
                created_at=datetime.now()
            )
            
            session.add(indicator)
            session.commit()
            logger.info(f"銘柄 {stock_code} のテクニカル指標を保存しました（スタイル: {investment_style}）")
            return True
                
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"テクニカル指標保存中にデータベースエラー: {e}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"テクニカル指標保存中にエラー: {e}")
            return False
        finally:
            session.close()
    
    def save_investment_decision(self, stock_code: str, decision_data: Dict, 
                               investment_style: str, analysis_date: date = None) -> bool:
        """投資判断をデータベースに保存"""
        session = self.Session()
        try:
            if analysis_date is None:
                analysis_date = date.today()
            
            # 投資スタイルの検証
            if investment_style not in self.investment_styles:
                logger.warning(f"無効な投資スタイル: {investment_style}")
                return False
            
            # 重複チェック
            existing = session.query(InvestmentDecision).filter(
                InvestmentDecision.stock_code == stock_code,
                InvestmentDecision.analysis_date == analysis_date,
                InvestmentDecision.investment_style == investment_style
            ).first()
            
            if existing:
                logger.info(f"銘柄 {stock_code} の投資判断は既に存在します（スタイル: {investment_style}）")
                return True
            
            # 新しいレコードを作成
            decision = InvestmentDecision(
                stock_code=stock_code,
                analysis_date=analysis_date,
                investment_style=investment_style,
                decision_type=decision_data.get('decision_type', 'analyze'),
                target_price=decision_data.get('target_price'),
                stop_loss=decision_data.get('stop_loss'),
                confidence_score=decision_data.get('confidence_score'),
                rsi_signal=decision_data.get('rsi_signal'),
                macd_signal=decision_data.get('macd_signal'),
                bb_signal=decision_data.get('bb_signal'),
                stoch_signal=decision_data.get('stoch_signal'),
                overall_signal=decision_data.get('overall_signal'),
                buy_count=decision_data.get('buy_count'),
                sell_count=decision_data.get('sell_count'),
                ai_reasoning=decision_data.get('ai_reasoning'),
                risk_assessment=decision_data.get('risk_assessment'),
                created_at=datetime.now()
            )
            
            session.add(decision)
            session.commit()
            logger.info(f"銘柄 {stock_code} の投資判断を保存しました（スタイル: {investment_style}）")
            return True
                
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"投資判断保存中にデータベースエラー: {e}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"投資判断保存中にエラー: {e}")
            return False
        finally:
            session.close()
    
    def save_backtest_result(self, stock_code: str, backtest_data: Dict, 
                           investment_style: str) -> bool:
        """バックテスト結果をデータベースに保存"""
        session = self.Session()
        try:
            # 投資スタイルの検証
            if investment_style not in self.investment_styles:
                logger.warning(f"無効な投資スタイル: {investment_style}")
                return False
            
            # 重複チェック
            existing = session.query(BacktestResult).filter(
                BacktestResult.stock_code == stock_code,
                BacktestResult.investment_style == investment_style,
                BacktestResult.strategy_name == backtest_data.get('strategy_name', 'default')
            ).first()
            
            if existing:
                logger.info(f"銘柄 {stock_code} のバックテスト結果は既に存在します（スタイル: {investment_style}）")
                return True
            
            # 新しいレコードを作成
            backtest = BacktestResult(
                stock_code=stock_code,
                investment_style=investment_style,
                strategy_name=backtest_data.get('strategy_name', 'default'),
                start_date=backtest_data.get('start_date'),
                end_date=backtest_data.get('end_date'),
                total_return=backtest_data.get('total_return'),
                annual_return=backtest_data.get('annual_return'),
                sharpe_ratio=backtest_data.get('sharpe_ratio'),
                max_drawdown=backtest_data.get('max_drawdown'),
                volatility=backtest_data.get('volatility'),
                win_rate=backtest_data.get('win_rate'),
                profit_factor=backtest_data.get('profit_factor'),
                total_trades=backtest_data.get('total_trades'),
                avg_trade_return=backtest_data.get('avg_trade_return'),
                benchmark_return=backtest_data.get('benchmark_return'),
                created_at=datetime.now()
            )
            
            session.add(backtest)
            session.commit()
            logger.info(f"銘柄 {stock_code} のバックテスト結果を保存しました（スタイル: {investment_style}）")
            return True
                
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"バックテスト結果保存中にデータベースエラー: {e}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"バックテスト結果保存中にエラー: {e}")
            return False
        finally:
            session.close()
    
    def get_historical_indicators(self, stock_code: str, days: int = 30, 
                                investment_style: str = None) -> List[Dict]:
        """過去のテクニカル指標を取得"""
        session = self.Session()
        try:
            query = session.query(TechnicalIndicator).filter(
                TechnicalIndicator.stock_code == stock_code
            )
            
            if investment_style:
                query = query.filter(TechnicalIndicator.investment_style == investment_style)
            
            indicators = query.order_by(
                TechnicalIndicator.analysis_date.desc()
            ).limit(days).all()
            
            result = []
            for indicator in indicators:
                result.append({
                    'stock_code': indicator.stock_code,
                    'analysis_date': indicator.analysis_date,
                    'investment_style': indicator.investment_style,
                    'current_price': float(indicator.current_price) if indicator.current_price else None,
                    'sma_5': float(indicator.sma_5) if indicator.sma_5 else None,
                    'sma_10': float(indicator.sma_10) if indicator.sma_10 else None,
                    'sma_20': float(indicator.sma_20) if indicator.sma_20 else None,
                    'sma_50': float(indicator.sma_50) if indicator.sma_50 else None,
                    'rsi_14': float(indicator.rsi_14) if indicator.rsi_14 else None,
                    'macd_line': float(indicator.macd_line) if indicator.macd_line else None,
                    'macd_signal': float(indicator.macd_signal) if indicator.macd_signal else None,
                    'macd_histogram': float(indicator.macd_histogram) if indicator.macd_histogram else None,
                    'bb_upper': float(indicator.bb_upper) if indicator.bb_upper else None,
                    'bb_middle': float(indicator.bb_middle) if indicator.bb_middle else None,
                    'bb_lower': float(indicator.bb_lower) if indicator.bb_lower else None,
                    'stoch_k': float(indicator.stoch_k) if indicator.stoch_k else None,
                    'stoch_d': float(indicator.stoch_d) if indicator.stoch_d else None,
                    'volume_ratio': float(indicator.volume_ratio) if indicator.volume_ratio else None,
                    'price_change_1d': float(indicator.price_change_1d) if indicator.price_change_1d else None,
                    'price_change_5d': float(indicator.price_change_5d) if indicator.price_change_5d else None,
                    'price_change_20d': float(indicator.price_change_20d) if indicator.price_change_20d else None,
                    'volatility_20d': float(indicator.volatility_20d) if indicator.volatility_20d else None,
                    'confidence_score': float(indicator.confidence_score) if indicator.confidence_score else None,
                    'analysis_version': indicator.analysis_version,
                    'created_at': indicator.created_at
                })
            
            logger.info(f"銘柄 {stock_code} の過去{len(result)}件の指標を取得しました")
            return result
                
        except SQLAlchemyError as e:
            logger.error(f"過去指標取得中にデータベースエラー: {e}")
            return []
        except Exception as e:
            logger.error(f"過去指標取得中にエラー: {e}")
            return []
        finally:
            session.close()
    
    def _calculate_confidence_score(self, indicators: Dict) -> float:
        """信頼度スコアを計算"""
        try:
            score = 0.5  # 基本スコア
            
            # データの完全性に基づくスコア調整
            valid_indicators = sum(1 for value in indicators.values() if value is not None)
            total_indicators = len(indicators)
            
            if total_indicators > 0:
                completeness_ratio = valid_indicators / total_indicators
                score += completeness_ratio * 0.3  # 完全性による最大+0.3
            
            # ボラティリティによる調整（低ボラティリティは信頼度向上）
            volatility = indicators.get('volatility_20d')
            if volatility is not None and volatility < 0.2:  # 20%未満のボラティリティ
                score += 0.1
            
            # スコアを0.0-1.0の範囲に制限
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.warning(f"信頼度スコア計算中にエラー: {e}")
            return 0.5
    
    def get_investment_style_display_name(self, style_code: str) -> str:
        """投資スタイルコードから表示名を取得"""
        return self.investment_styles.get(style_code, style_code)
