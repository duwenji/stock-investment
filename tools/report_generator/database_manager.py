#!/usr/bin/env python3
"""
データベース操作モジュール
MCPサーバを使用して分析結果をデータベースに保存
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, date
import json

logger = logging.getLogger(__name__)

class AnalysisDataManager:
    """分析データ管理クラス"""
    
    def __init__(self):
        self.investment_styles = {
            'day_trading': 'デイトレード',
            'swing_trading': 'スイングトレード', 
            'long_term': '長期投資'
        }
    
    def save_technical_indicators(self, stock_code: str, indicators: Dict, 
                                investment_style: str, analysis_date: date = None) -> bool:
        """テクニカル指標をデータベースに保存"""
        try:
            if analysis_date is None:
                analysis_date = date.today()
            
            # 投資スタイルの検証
            if investment_style not in self.investment_styles:
                logger.warning(f"無効な投資スタイル: {investment_style}")
                return False
            
            # 信頼度スコアの計算
            confidence_score = self._calculate_confidence_score(indicators)
            
            # データの準備
            indicator_data = {
                'stock_code': stock_code,
                'analysis_date': analysis_date.isoformat(),
                'investment_style': investment_style,
                'current_price': indicators.get('current_price'),
                'sma_5': indicators.get('sma_5'),
                'sma_10': indicators.get('sma_10'),
                'sma_20': indicators.get('sma_20'),
                'sma_50': indicators.get('sma_50'),
                'rsi_14': indicators.get('rsi_14'),
                'macd_line': indicators.get('macd_line'),
                'macd_signal': indicators.get('macd_signal'),
                'macd_histogram': indicators.get('macd_histogram'),
                'bb_upper': indicators.get('bb_upper'),
                'bb_middle': indicators.get('bb_middle'),
                'bb_lower': indicators.get('bb_lower'),
                'stoch_k': indicators.get('stoch_k'),
                'stoch_d': indicators.get('stoch_d'),
                'volume_ratio': indicators.get('volume_ratio'),
                'price_change_1d': indicators.get('price_change_1d'),
                'price_change_5d': indicators.get('price_change_5d'),
                'price_change_20d': indicators.get('price_change_20d'),
                'volatility_20d': indicators.get('volatility_20d'),
                'confidence_score': confidence_score,
                'analysis_version': 'v1.0'
            }
            
            # データベースに保存
            result = self._execute_mcp_create('technical_indicators', indicator_data)
            
            if result.get('success'):
                logger.info(f"銘柄 {stock_code} のテクニカル指標を保存しました（スタイル: {investment_style}）")
                return True
            else:
                logger.error(f"テクニカル指標の保存に失敗: {result.get('message', '不明なエラー')}")
                return False
                
        except Exception as e:
            logger.error(f"テクニカル指標保存中にエラー: {e}")
            return False
    
    def save_investment_decision(self, stock_code: str, decision_data: Dict, 
                               investment_style: str, analysis_date: date = None) -> bool:
        """投資判断をデータベースに保存"""
        try:
            if analysis_date is None:
                analysis_date = date.today()
            
            # 投資スタイルの検証
            if investment_style not in self.investment_styles:
                logger.warning(f"無効な投資スタイル: {investment_style}")
                return False
            
            # データの準備
            decision_record = {
                'stock_code': stock_code,
                'analysis_date': analysis_date.isoformat(),
                'investment_style': investment_style,
                'decision_type': decision_data.get('decision_type', 'analyze'),
                'target_price': decision_data.get('target_price'),
                'stop_loss': decision_data.get('stop_loss'),
                'confidence_score': decision_data.get('confidence_score'),
                'rsi_signal': decision_data.get('rsi_signal'),
                'macd_signal': decision_data.get('macd_signal'),
                'bb_signal': decision_data.get('bb_signal'),
                'stoch_signal': decision_data.get('stoch_signal'),
                'overall_signal': decision_data.get('overall_signal'),
                'buy_count': decision_data.get('buy_count'),
                'sell_count': decision_data.get('sell_count'),
                'ai_reasoning': decision_data.get('ai_reasoning'),
                'risk_assessment': decision_data.get('risk_assessment')
            }
            
            # データベースに保存
            result = self._execute_mcp_create('investment_decisions', decision_record)
            
            if result.get('success'):
                logger.info(f"銘柄 {stock_code} の投資判断を保存しました（スタイル: {investment_style}）")
                return True
            else:
                logger.error(f"投資判断の保存に失敗: {result.get('message', '不明なエラー')}")
                return False
                
        except Exception as e:
            logger.error(f"投資判断保存中にエラー: {e}")
            return False
    
    def save_backtest_result(self, stock_code: str, backtest_data: Dict, 
                           investment_style: str) -> bool:
        """バックテスト結果をデータベースに保存"""
        try:
            # データの準備
            backtest_record = {
                'stock_code': stock_code,
                'investment_style': investment_style,
                'strategy_name': backtest_data.get('strategy_name', 'default'),
                'start_date': backtest_data.get('start_date'),
                'end_date': backtest_data.get('end_date'),
                'total_return': backtest_data.get('total_return'),
                'annual_return': backtest_data.get('annual_return'),
                'sharpe_ratio': backtest_data.get('sharpe_ratio'),
                'max_drawdown': backtest_data.get('max_drawdown'),
                'volatility': backtest_data.get('volatility'),
                'win_rate': backtest_data.get('win_rate'),
                'profit_factor': backtest_data.get('profit_factor'),
                'total_trades': backtest_data.get('total_trades'),
                'avg_trade_return': backtest_data.get('avg_trade_return'),
                'benchmark_return': backtest_data.get('benchmark_return')
            }
            
            # データベースに保存
            result = self._execute_mcp_create('backtest_results', backtest_record)
            
            if result.get('success'):
                logger.info(f"銘柄 {stock_code} のバックテスト結果を保存しました（スタイル: {investment_style}）")
                return True
            else:
                logger.error(f"バックテスト結果の保存に失敗: {result.get('message', '不明なエラー')}")
                return False
                
        except Exception as e:
            logger.error(f"バックテスト結果保存中にエラー: {e}")
            return False
    
    def get_historical_indicators(self, stock_code: str, days: int = 30, 
                                investment_style: str = None) -> List[Dict]:
        """過去のテクニカル指標を取得"""
        try:
            conditions = {
                'stock_code': stock_code
            }
            
            if investment_style:
                conditions['investment_style'] = investment_style
            
            result = self._execute_mcp_read(
                'technical_indicators', 
                conditions=conditions,
                order_by='analysis_date',
                order_direction='DESC',
                limit=days
            )
            
            if result.get('success'):
                return result.get('data', [])
            else:
                logger.error(f"過去指標の取得に失敗: {result.get('message', '不明なエラー')}")
                return []
                
        except Exception as e:
            logger.error(f"過去指標取得中にエラー: {e}")
            return []
    
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
    
    def _execute_mcp_create(self, table_name: str, data: Dict) -> Dict:
        """MCPサーバを使用してデータを作成"""
        # この関数は実際のMCPツール呼び出しをシミュレート
        # 実際の実装ではMCPツールを使用
        logger.debug(f"データベース作成: {table_name} - {data}")
        return {'success': True, 'message': '作成成功'}
    
    def _execute_mcp_read(self, table_name: str, conditions: Dict = None, 
                         order_by: str = None, order_direction: str = 'ASC',
                         limit: int = 100) -> Dict:
        """MCPサーバを使用してデータを読み取り"""
        # この関数は実際のMCPツール呼び出しをシミュレート
        # 実際の実装ではMCPツールを使用
        logger.debug(f"データベース読み取り: {table_name} - {conditions}")
        return {'success': True, 'data': []}
    
    def get_investment_style_display_name(self, style_code: str) -> str:
        """投資スタイルコードから表示名を取得"""
        return self.investment_styles.get(style_code, style_code)
