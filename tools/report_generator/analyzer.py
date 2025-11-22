#!/usr/bin/env python3
"""
銘柄レポート生成用分析モジュール
短期トレード向けのテクニカル指標を計算
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
import sys
import os

# モジュールのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database_manager import AnalysisDataManager

logger = logging.getLogger(__name__)

class StockAnalyzer:
    """株式分析クラス"""
    
    def __init__(self):
        self.indicators = {}
        self.db_manager = AnalysisDataManager()
    
    def calculate_technical_indicators(self, price_data: pd.DataFrame) -> Dict:
        """テクニカル指標を計算"""
        if price_data is None or price_data.empty:
            return {}
        
        try:
            # 終値データを取得
            close_prices = price_data['close_price'].dropna()
            high_prices = price_data['high_price'].dropna()
            low_prices = price_data['low_price'].dropna()
            volumes = price_data['volume'].dropna()
            
            if len(close_prices) < 20:
                logger.warning("株価データが少なすぎます（20日以上必要）")
                return {}
            
            indicators = {}
            
            # 1. 移動平均
            indicators['sma_5'] = self._calculate_sma(close_prices, 5)
            indicators['sma_10'] = self._calculate_sma(close_prices, 10)
            indicators['sma_20'] = self._calculate_sma(close_prices, 20)
            indicators['sma_50'] = self._calculate_sma(close_prices, 50)
            
            # 2. RSI (相対力指数)
            indicators['rsi_14'] = self._calculate_rsi(close_prices, 14)
            
            # 3. MACD (移動平均収束拡散)
            macd_line, macd_signal, macd_histogram = self._calculate_macd(close_prices)
            indicators['macd_line'] = macd_line
            indicators['macd_signal'] = macd_signal
            indicators['macd_histogram'] = macd_histogram
            
            # 4. ボリンジャーバンド
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close_prices, 20)
            indicators['bb_upper'] = bb_upper
            indicators['bb_middle'] = bb_middle
            indicators['bb_lower'] = bb_lower
            
            # 5. ストキャスティクス
            stoch_k, stoch_d = self._calculate_stochastic(high_prices, low_prices, close_prices, 14, 3)
            indicators['stoch_k'] = stoch_k
            indicators['stoch_d'] = stoch_d
            
            # 6. 出来高分析
            indicators['volume_sma_20'] = self._calculate_sma(volumes, 20)
            indicators['volume_ratio'] = self._calculate_volume_ratio(volumes, 20)
            
            # 7. 価格変動分析
            indicators['price_change_1d'] = self._calculate_price_change(close_prices, 1)
            indicators['price_change_5d'] = self._calculate_price_change(close_prices, 5)
            indicators['price_change_20d'] = self._calculate_price_change(close_prices, 20)
            
            # 8. ボラティリティ
            indicators['volatility_20d'] = self._calculate_volatility(close_prices, 20)
            
            # 最新値のみを返す
            latest_indicators = {}
            for key, values in indicators.items():
                if values is not None and len(values) > 0:
                    latest_indicators[key] = values.iloc[-1] if hasattr(values, 'iloc') else values[-1]
                else:
                    latest_indicators[key] = None
            
            return latest_indicators
            
        except Exception as e:
            logger.error(f"テクニカル指標計算中にエラー: {e}")
            return {}
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """単純移動平均を計算"""
        return prices.rolling(window=period).mean()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSIを計算"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACDを計算"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        macd_signal = macd_line.ewm(span=9).mean()
        macd_histogram = macd_line - macd_signal
        return macd_line, macd_signal, macd_histogram
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """ボリンジャーバンドを計算"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        bb_upper = sma + (std * 2)
        bb_lower = sma - (std * 2)
        return bb_upper, sma, bb_lower
    
    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                            k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """ストキャスティクスを計算"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        stoch_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        stoch_d = stoch_k.rolling(window=d_period).mean()
        return stoch_k, stoch_d
    
    def _calculate_volume_ratio(self, volumes: pd.Series, period: int = 20) -> pd.Series:
        """出来高比率を計算"""
        volume_sma = volumes.rolling(window=period).mean()
        return volumes / volume_sma
    
    def _calculate_price_change(self, prices: pd.Series, period: int) -> pd.Series:
        """価格変動率を計算"""
        return ((prices / prices.shift(period)) - 1) * 100
    
    def _calculate_volatility(self, prices: pd.Series, period: int) -> pd.Series:
        """ボラティリティ（標準偏差）を計算"""
        returns = prices.pct_change()
        return returns.rolling(window=period).std() * np.sqrt(252)  # 年率換算
    
    def generate_trading_signals(self, indicators: Dict, current_price: float) -> Dict:
        """トレードシグナルを生成"""
        signals = {}
        
        try:
            # RSIシグナル
            rsi = indicators.get('rsi_14')
            if rsi is not None:
                if rsi > 70:
                    signals['rsi_signal'] = '売り'
                    signals['rsi_strength'] = '強い'
                elif rsi < 30:
                    signals['rsi_signal'] = '買い'
                    signals['rsi_strength'] = '強い'
                else:
                    signals['rsi_signal'] = '中立'
                    signals['rsi_strength'] = '弱い'
            
            # MACDシグナル
            macd_line = indicators.get('macd_line')
            macd_signal = indicators.get('macd_signal')
            if macd_line is not None and macd_signal is not None:
                if macd_line > macd_signal and indicators.get('macd_histogram', 0) > 0:
                    signals['macd_signal'] = '買い'
                elif macd_line < macd_signal and indicators.get('macd_histogram', 0) < 0:
                    signals['macd_signal'] = '売り'
                else:
                    signals['macd_signal'] = '中立'
            
            # ボリンジャーバンドシグナル
            bb_upper = indicators.get('bb_upper')
            bb_lower = indicators.get('bb_lower')
            if bb_upper is not None and bb_lower is not None and current_price:
                if current_price >= bb_upper:
                    signals['bb_signal'] = '売り（上方ブレイクアウト）'
                elif current_price <= bb_lower:
                    signals['bb_signal'] = '買い（下方ブレイクアウト）'
                else:
                    signals['bb_signal'] = '中立'
            
            # ストキャスティクスシグナル
            stoch_k = indicators.get('stoch_k')
            stoch_d = indicators.get('stoch_d')
            if stoch_k is not None and stoch_d is not None:
                if stoch_k > 80 and stoch_d > 80:
                    signals['stoch_signal'] = '売り'
                elif stoch_k < 20 and stoch_d < 20:
                    signals['stoch_signal'] = '買い'
                else:
                    signals['stoch_signal'] = '中立'
            
            # 総合評価
            buy_signals = sum(1 for signal in signals.values() if '買い' in str(signal))
            sell_signals = sum(1 for signal in signals.values() if '売り' in str(signal))
            
            if buy_signals > sell_signals:
                signals['overall_signal'] = '買い推奨'
            elif sell_signals > buy_signals:
                signals['overall_signal'] = '売り推奨'
            else:
                signals['overall_signal'] = '中立'
            
            signals['buy_count'] = buy_signals
            signals['sell_count'] = sell_signals
            
            return signals
            
        except Exception as e:
            logger.error(f"トレードシグナル生成中にエラー: {e}")
            return {}
    
    def analyze_stock_by_style(self, stock_data: Dict, investment_style: str) -> Dict:
        """投資スタイル別に銘柄分析を実行"""
        try:
            stock_code = stock_data['stock_code']
            price_history = stock_data['price_history']
            basic_info = stock_data['basic_info']
            
            # DataFrameの空チェックを修正
            if price_history is None or (hasattr(price_history, 'empty') and price_history.empty):
                logger.warning(f"銘柄 {stock_code} の株価データがありません")
                return {}
            
            # 現在価格を取得
            current_price = price_history['close_price'].iloc[-1] if len(price_history) > 0 else None
            
            # 投資スタイル別のテクニカル指標を計算
            indicators = self.calculate_technical_indicators_by_style(price_history, investment_style)
            
            # 投資スタイル別のトレードシグナルを生成
            signals = self.generate_trading_signals_by_style(indicators, current_price, investment_style)
            
            # AI分析による総合判断
            ai_analysis = self.generate_ai_analysis(indicators, signals, investment_style)
            
            # 分析結果をまとめる
            analysis_result = {
                'stock_code': stock_code,
                'current_price': current_price,
                'indicators': indicators,
                'signals': signals,
                'ai_analysis': ai_analysis,
                'investment_style': investment_style,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # データベースに保存
            self._save_analysis_to_database(analysis_result)
            
            logger.info(f"銘柄 {stock_code} の{self.db_manager.get_investment_style_display_name(investment_style)}分析完了")
            return analysis_result
            
        except Exception as e:
            logger.error(f"銘柄 {stock_code} の{investment_style}分析中にエラー: {e}")
            return {}
    
    def analyze_stock(self, stock_data: Dict) -> Dict:
        """銘柄の総合分析を実行（従来の方法 - 互換性維持）"""
        try:
            stock_code = stock_data['stock_code']
            price_history = stock_data['price_history']
            basic_info = stock_data['basic_info']
            
            # DataFrameの空チェックを修正
            if price_history is None or (hasattr(price_history, 'empty') and price_history.empty):
                logger.warning(f"銘柄 {stock_code} の株価データがありません")
                return {}
            
            # 現在価格を取得
            current_price = price_history['close_price'].iloc[-1] if len(price_history) > 0 else None
            
            # テクニカル指標を計算
            indicators = self.calculate_technical_indicators(price_history)
            
            # トレードシグナルを生成
            signals = self.generate_trading_signals(indicators, current_price)
            
            # 分析結果をまとめる
            analysis_result = {
                'stock_code': stock_code,
                'current_price': current_price,
                'indicators': indicators,
                'signals': signals,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"銘柄 {stock_code} の分析完了")
            return analysis_result
            
        except Exception as e:
            logger.error(f"銘柄 {stock_code} の分析中にエラー: {e}")
            return {}
    
    def calculate_technical_indicators_by_style(self, price_data: pd.DataFrame, investment_style: str) -> Dict:
        """投資スタイル別にテクニカル指標を計算"""
        base_indicators = self.calculate_technical_indicators(price_data)
        
        if investment_style == 'day_trading':
            # デイトレード: 短期指標を重視
            return self._enhance_for_day_trading(base_indicators, price_data)
        elif investment_style == 'swing_trading':
            # スイングトレード: 中期指標を重視
            return self._enhance_for_swing_trading(base_indicators, price_data)
        elif investment_style == 'long_term':
            # 長期投資: 長期指標とファンダメンタルを重視
            return self._enhance_for_long_term(base_indicators, price_data)
        else:
            return base_indicators
    
    def generate_trading_signals_by_style(self, indicators: Dict, current_price: float, investment_style: str) -> Dict:
        """投資スタイル別にトレードシグナルを生成"""
        base_signals = self.generate_trading_signals(indicators, current_price)
        
        if investment_style == 'day_trading':
            # デイトレード: 短期シグナルを重視
            return self._adjust_signals_for_day_trading(base_signals, indicators)
        elif investment_style == 'swing_trading':
            # スイングトレード: トレンドシグナルを重視
            return self._adjust_signals_for_swing_trading(base_signals, indicators)
        elif investment_style == 'long_term':
            # 長期投資: 長期シグナルとリスク評価を重視
            return self._adjust_signals_for_long_term(base_signals, indicators)
        else:
            return base_signals
    
    def _enhance_for_day_trading(self, base_indicators: Dict, price_data: pd.DataFrame) -> Dict:
        """デイトレード用に指標を強化"""
        enhanced = base_indicators.copy()
        
        try:
            # 短期ボラティリティの追加
            close_prices = price_data['close_price'].dropna()
            if len(close_prices) >= 5:
                volatility_5d = self._calculate_volatility(close_prices, 5)
                if volatility_5d is not None and len(volatility_5d) > 0:
                    enhanced['volatility_5d'] = volatility_5d.iloc[-1] if hasattr(volatility_5d, 'iloc') else volatility_5d[-1]
            
            # 短期RSIの追加
            if len(close_prices) >= 7:
                rsi_7 = self._calculate_rsi(close_prices, 7)
                if rsi_7 is not None and len(rsi_7) > 0:
                    enhanced['rsi_7'] = rsi_7.iloc[-1] if hasattr(rsi_7, 'iloc') else rsi_7[-1]
            
            # 価格変動の短期指標
            enhanced['price_change_1h'] = None  # 1時間足データがあれば計算
            enhanced['intraday_volatility'] = None  # 日内変動率
            
        except Exception as e:
            logger.warning(f"デイトレード指標強化中にエラー: {e}")
        
        return enhanced
    
    def _enhance_for_swing_trading(self, base_indicators: Dict, price_data: pd.DataFrame) -> Dict:
        """スイングトレード用に指標を強化"""
        enhanced = base_indicators.copy()
        
        try:
            # 中期トレンド指標の追加
            close_prices = price_data['close_price'].dropna()
            if len(close_prices) >= 50:
                enhanced['sma_100'] = self._calculate_sma(close_prices, 100)
                enhanced['trend_strength'] = self._calculate_trend_strength(close_prices)
            
            # サポート/レジスタンスレベルの特定
            enhanced['support_level'] = self._identify_support_level(close_prices)
            enhanced['resistance_level'] = self._identify_resistance_level(close_prices)
            
        except Exception as e:
            logger.warning(f"スイングトレード指標強化中にエラー: {e}")
        
        return enhanced
    
    def _enhance_for_long_term(self, base_indicators: Dict, price_data: pd.DataFrame) -> Dict:
        """長期投資用に指標を強化"""
        enhanced = base_indicators.copy()
        
        try:
            # 長期トレンドとボラティリティ
            close_prices = price_data['close_price'].dropna()
            if len(close_prices) >= 200:
                enhanced['sma_200'] = self._calculate_sma(close_prices, 200)
                enhanced['volatility_1y'] = self._calculate_volatility(close_prices, min(252, len(close_prices)))
            
            # 長期リターン指標
            if len(close_prices) >= 252:
                enhanced['annual_return'] = self._calculate_annual_return(close_prices)
                enhanced['max_drawdown_1y'] = self._calculate_max_drawdown(close_prices)
            
        except Exception as e:
            logger.warning(f"長期投資指標強化中にエラー: {e}")
        
        return enhanced
    
    def _adjust_signals_for_day_trading(self, base_signals: Dict, indicators: Dict) -> Dict:
        """デイトレード用にシグナルを調整"""
        adjusted = base_signals.copy()
        
        # 短期指標の重みを増加
        rsi = indicators.get('rsi_14')
        if rsi is not None:
            if rsi > 75:
                adjusted['rsi_signal'] = '強い売り'
            elif rsi < 25:
                adjusted['rsi_signal'] = '強い買い'
        
        # ボラティリティ考慮
        volatility = indicators.get('volatility_5d')
        if volatility is not None and volatility > 0.3:  # 30%以上のボラティリティ
            adjusted['risk_note'] = '高ボラティリティ注意'
        
        return adjusted
    
    def _adjust_signals_for_swing_trading(self, base_signals: Dict, indicators: Dict) -> Dict:
        """スイングトレード用にシグナルを調整"""
        adjusted = base_signals.copy()
        
        # トレンドの強さを考慮
        trend_strength = indicators.get('trend_strength')
        if trend_strength is not None and trend_strength > 0.7:
            if adjusted.get('overall_signal') == '買い推奨':
                adjusted['overall_signal'] = '強い買い推奨（強気トレンド）'
            elif adjusted.get('overall_signal') == '売り推奨':
                adjusted['overall_signal'] = '強い売り推奨（弱気トレンド）'
        
        # サポート/レジスタンス考慮
        support = indicators.get('support_level')
        resistance = indicators.get('resistance_level')
        if support and resistance:
            adjusted['key_levels'] = f"サポート: {support:.2f}, レジスタンス: {resistance:.2f}"
        
        return adjusted
    
    def _adjust_signals_for_long_term(self, base_signals: Dict, indicators: Dict) -> Dict:
        """長期投資用にシグナルを調整"""
        adjusted = base_signals.copy()
        
        # 長期トレンド考慮
        sma_200 = indicators.get('sma_200')
        current_price = indicators.get('current_price')
        if sma_200 is not None and current_price is not None:
            if current_price > sma_200:
                adjusted['long_term_trend'] = '強気（200日移動平均以上）'
            else:
                adjusted['long_term_trend'] = '弱気（200日移動平均以下）'
        
        # リスク評価
        max_drawdown = indicators.get('max_drawdown_1y')
        if max_drawdown is not None:
            if max_drawdown > 0.3:  # 30%以上の最大ドローダウン
                adjusted['risk_assessment'] = '高リスク'
            elif max_drawdown > 0.15:  # 15%以上の最大ドローダウン
                adjusted['risk_assessment'] = '中リスク'
            else:
                adjusted['risk_assessment'] = '低リスク'
        
        return adjusted
    
    def generate_ai_analysis(self, indicators: Dict, signals: Dict, investment_style: str) -> Dict:
        """AIによる総合分析を生成"""
        try:
            # 信頼度スコアの計算
            confidence_score = self._calculate_ai_confidence(indicators, signals)
            
            # 投資スタイルに基づく推奨
            recommendation = self._generate_ai_recommendation(indicators, signals, investment_style)
            
            # リスク評価
            risk_assessment = self._assess_ai_risk(indicators, investment_style)
            
            return {
                'confidence_score': confidence_score,
                'recommendation': recommendation,
                'reasoning': self._generate_ai_reasoning(indicators, signals, investment_style),
                'risk_assessment': risk_assessment,
                'time_horizon': self._get_time_horizon(investment_style)
            }
            
        except Exception as e:
            logger.error(f"AI分析生成中にエラー: {e}")
            return {
                'confidence_score': 0.5,
                'recommendation': '分析エラー',
                'reasoning': f'分析中にエラーが発生しました: {e}',
                'risk_assessment': '不明',
                'time_horizon': '不明'
            }
    
    def _calculate_ai_confidence(self, indicators: Dict, signals: Dict) -> float:
        """AI分析の信頼度スコアを計算"""
        try:
            score = 0.5
            
            # データの完全性
            valid_indicators = sum(1 for value in indicators.values() if value is not None)
            total_indicators = len(indicators)
            if total_indicators > 0:
                completeness = valid_indicators / total_indicators
                score += completeness * 0.2
            
            # シグナルの一貫性
            buy_count = signals.get('buy_count', 0)
            sell_count = signals.get('sell_count', 0)
            total_signals = buy_count + sell_count
            if total_signals > 0:
                consistency = abs(buy_count - sell_count) / total_signals
                score += consistency * 0.3
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.warning(f"信頼度スコア計算中にエラー: {e}")
            return 0.5
    
    def _generate_ai_recommendation(self, indicators: Dict, signals: Dict, investment_style: str) -> str:
        """AIによる投資推奨を生成"""
        overall_signal = signals.get('overall_signal', '中立')
        confidence = self._calculate_ai_confidence(indicators, signals)
        
        if confidence < 0.3:
            return f"信頼度低: {overall_signal}（データ不足）"
        elif confidence < 0.7:
            return f"信頼度中: {overall_signal}"
        else:
            return f"信頼度高: {overall_signal}"
    
    def _generate_ai_reasoning(self, indicators: Dict, signals: Dict, investment_style: str) -> str:
        """AI分析の根拠を生成"""
        reasoning_parts = []
        
        # 主要指標の状態
        rsi = indicators.get('rsi_14')
        if rsi is not None:
            if rsi > 70:
                reasoning_parts.append("RSIが売りゾーン")
            elif rsi < 30:
                reasoning_parts.append("RSIが買いゾーン")
        
        macd_histogram = indicators.get('macd_histogram')
        if macd_histogram is not None:
            if macd_histogram > 0:
                reasoning_parts.append("MACDが強気")
            else:
                reasoning_parts.append("MACDが弱気")
        
        # 投資スタイルに応じた説明
        if investment_style == 'day_trading':
            reasoning_parts.append("短期取引向け分析")
        elif investment_style == 'swing_trading':
            reasoning_parts.append("中期トレンド重視")
        elif investment_style == 'long_term':
            reasoning_parts.append("長期投資視点")
        
        return "、".join(reasoning_parts) if reasoning_parts else "指標に明確なシグナルなし"
    
    def _assess_ai_risk(self, indicators: Dict, investment_style: str) -> str:
        """AIによるリスク評価"""
        volatility = indicators.get('volatility_20d')
        if volatility is None:
            return "リスク評価不可"
        
        if volatility > 0.4:
            return "高リスク"
        elif volatility > 0.2:
            return "中リスク"
        else:
            return "低リスク"
    
    def _get_time_horizon(self, investment_style: str) -> str:
        """投資スタイルに応じた時間軸を取得"""
        if investment_style == 'day_trading':
            return "短期（数日以内）"
        elif investment_style == 'swing_trading':
            return "中期（数週間～数ヶ月）"
        elif investment_style == 'long_term':
            return "長期（数ヶ月～数年）"
        else:
            return "不明"
    
    def _save_analysis_to_database(self, analysis_result: Dict):
        """分析結果をデータベースに保存"""
        try:
            stock_code = analysis_result['stock_code']
            investment_style = analysis_result['investment_style']
            indicators = analysis_result['indicators']
            signals = analysis_result['signals']
            ai_analysis = analysis_result['ai_analysis']
            
            # テクニカル指標を保存
            self.db_manager.save_technical_indicators(
                stock_code, indicators, investment_style
            )
            
            # 投資判断を保存
            decision_data = {
                'decision_type': 'analyze',
                'target_price': None,  # 必要に応じて設定
                'stop_loss': None,     # 必要に応じて設定
                'confidence_score': ai_analysis.get('confidence_score'),
                'rsi_signal': signals.get('rsi_signal'),
                'macd_signal': signals.get('macd_signal'),
                'bb_signal': signals.get('bb_signal'),
                'stoch_signal': signals.get('stoch_signal'),
                'overall_signal': signals.get('overall_signal'),
                'buy_count': signals.get('buy_count'),
                'sell_count': signals.get('sell_count'),
                'ai_reasoning': ai_analysis.get('reasoning'),
                'risk_assessment': ai_analysis.get('risk_assessment')
            }
            
            self.db_manager.save_investment_decision(
                stock_code, decision_data, investment_style
            )
            
            logger.info(f"銘柄 {stock_code} の分析結果をデータベースに保存しました")
            
        except Exception as e:
            logger.error(f"分析結果のデータベース保存中にエラー: {e}")
    
    def _calculate_trend_strength(self, prices: pd.Series) -> float:
        """トレンドの強さを計算"""
        try:
            if len(prices) < 20:
                return 0.0
            
            # 短期と長期の移動平均の差でトレンド強度を計算
            sma_short = prices.rolling(window=10).mean()
            sma_long = prices.rolling(window=50).mean()
            
            if len(sma_short) < 1 or len(sma_long) < 1:
                return 0.0
            
            # 最新値の差を正規化
            diff = abs(sma_short.iloc[-1] - sma_long.iloc[-1])
            avg_price = (sma_short.iloc[-1] + sma_long.iloc[-1]) / 2
            
            if avg_price == 0:
                return 0.0
            
            return min(1.0, diff / avg_price)
            
        except Exception as e:
            logger.warning(f"トレンド強度計算中にエラー: {e}")
            return 0.0
    
    def _identify_support_level(self, prices: pd.Series) -> Optional[float]:
        """サポートレベルを特定"""
        try:
            if len(prices) < 20:
                return None
            
            # 単純化: 直近20日間の最安値
            return prices.tail(20).min()
            
        except Exception as e:
            logger.warning(f"サポートレベル特定中にエラー: {e}")
            return None
    
    def _identify_resistance_level(self, prices: pd.Series) -> Optional[float]:
        """レジスタンスレベルを特定"""
        try:
            if len(prices) < 20:
                return None
            
            # 単純化: 直近20日間の最高値
            return prices.tail(20).max()
            
        except Exception as e:
            logger.warning(f"レジスタンスレベル特定中にエラー: {e}")
            return None
    
    def _calculate_annual_return(self, prices: pd.Series) -> Optional[float]:
        """年率リターンを計算"""
        try:
            if len(prices) < 252:
                return None
            
            start_price = prices.iloc[0]
            end_price = prices.iloc[-1]
            
            if start_price == 0:
                return None
            
            total_return = (end_price - start_price) / start_price
            years = len(prices) / 252  # 取引日数ベース
            
            if years == 0:
                return None
            
            annual_return = (1 + total_return) ** (1 / years) - 1
            return annual_return
            
        except Exception as e:
            logger.warning(f"年率リターン計算中にエラー: {e}")
            return None
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> Optional[float]:
        """最大ドローダウンを計算"""
        try:
            if len(prices) < 2:
                return None
            
            cumulative_max = prices.expanding().max()
            drawdown = (prices - cumulative_max) / cumulative_max
            max_drawdown = drawdown.min()
            
            return abs(max_drawdown) if max_drawdown < 0 else 0.0
            
        except Exception as e:
            logger.warning(f"最大ドローダウン計算中にエラー: {e}")
            return None
