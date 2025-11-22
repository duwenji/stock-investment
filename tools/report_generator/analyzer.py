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

logger = logging.getLogger(__name__)

class StockAnalyzer:
    """株式分析クラス"""
    
    def __init__(self):
        self.indicators = {}
    
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
    
    def analyze_stock(self, stock_data: Dict) -> Dict:
        """銘柄の総合分析を実行"""
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
