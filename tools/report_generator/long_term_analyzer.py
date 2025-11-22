#!/usr/bin/env python3
"""
長期トレード向け分析モジュール
長期投資向けのテクニカル指標とファンダメンタル分析を計算
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LongTermStockAnalyzer:
    """長期株式分析クラス"""
    
    def __init__(self):
        self.indicators = {}
    
    def calculate_long_term_indicators(self, price_data: pd.DataFrame) -> Dict:
        """長期トレード向けテクニカル指標を計算"""
        if price_data is None or price_data.empty:
            logger.warning("株価データが空です")
            return {}
        
        try:
            # 終値データを取得
            close_prices = price_data['close_price'].dropna()
            high_prices = price_data['high_price'].dropna()
            low_prices = price_data['low_price'].dropna()
            volumes = price_data['volume'].dropna()
            
            # データ不足時の動的対応
            data_length = len(close_prices)
            logger.info(f"利用可能なデータ日数: {data_length}日")
            
            if data_length < 50:
                logger.warning("長期分析には最低50日以上の株価データが必要です")
                return self._calculate_limited_indicators(close_prices, high_prices, low_prices, volumes, data_length)
            
            # データ期間に応じた指標計算
            indicators = {}
            
            # 1. 長期移動平均（利用可能な期間で計算）
            if data_length >= 50:
                indicators['sma_50'] = self._calculate_sma(close_prices, 50)
            if data_length >= 100:
                indicators['sma_100'] = self._calculate_sma(close_prices, 100)
            if data_length >= 200:
                indicators['sma_200'] = self._calculate_sma(close_prices, 200)
            
            # 2. 指数移動平均（利用可能な期間で計算）
            if data_length >= 50:
                indicators['ema_50'] = self._calculate_ema(close_prices, 50)
            if data_length >= 100:
                indicators['ema_100'] = self._calculate_ema(close_prices, 100)
            if data_length >= 200:
                indicators['ema_200'] = self._calculate_ema(close_prices, 200)
            
            # 3. 長期RSI（利用可能な期間で計算）
            if data_length >= 26:
                indicators['rsi_26'] = self._calculate_rsi(close_prices, 26)
            if data_length >= 52:
                indicators['rsi_52'] = self._calculate_rsi(close_prices, 52)
            
            # 4. 長期ボリンジャーバンド（利用可能な期間で計算）
            if data_length >= 50:
                bb_upper_50, bb_middle_50, bb_lower_50 = self._calculate_bollinger_bands(close_prices, 50)
                indicators['bb_upper_50'] = bb_upper_50
                indicators['bb_middle_50'] = bb_middle_50
                indicators['bb_lower_50'] = bb_lower_50
            
            # 5. 長期MACD（利用可能な期間で計算）
            if data_length >= 26:
                macd_line_26, macd_signal_26, macd_histogram_26 = self._calculate_macd_long_term(close_prices)
                indicators['macd_line_26'] = macd_line_26
                indicators['macd_signal_26'] = macd_signal_26
                indicators['macd_histogram_26'] = macd_histogram_26
            
            # 6. 長期ストキャスティクス（利用可能な期間で計算）
            if data_length >= 26:
                stoch_k_26, stoch_d_26 = self._calculate_stochastic(high_prices, low_prices, close_prices, 26, 9)
                indicators['stoch_k_26'] = stoch_k_26
                indicators['stoch_d_26'] = stoch_d_26
            
            # 7. 長期価格変動分析（利用可能な期間で計算）
            if data_length >= 50:
                indicators['price_change_50d'] = self._calculate_price_change(close_prices, 50)
            if data_length >= 100:
                indicators['price_change_100d'] = self._calculate_price_change(close_prices, 100)
            if data_length >= 200:
                indicators['price_change_200d'] = self._calculate_price_change(close_prices, 200)
            if data_length >= 252:
                indicators['price_change_1y'] = self._calculate_price_change(close_prices, 252)
            
            # 8. 長期ボラティリティ（利用可能な期間で計算）
            if data_length >= 50:
                indicators['volatility_50d'] = self._calculate_volatility(close_prices, 50)
            if data_length >= 100:
                indicators['volatility_100d'] = self._calculate_volatility(close_prices, 100)
            if data_length >= 200:
                indicators['volatility_200d'] = self._calculate_volatility(close_prices, 200)
            
            # 9. トレンド分析（利用可能な期間で計算）
            if data_length >= 200:
                indicators['trend_strength'] = self._calculate_trend_strength(close_prices, 200)
                indicators['trend_direction'] = self._calculate_trend_direction(close_prices, 200)
            elif data_length >= 100:
                indicators['trend_strength'] = self._calculate_trend_strength(close_prices, 100)
                indicators['trend_direction'] = self._calculate_trend_direction(close_prices, 100)
            elif data_length >= 50:
                indicators['trend_strength'] = self._calculate_trend_strength(close_prices, 50)
                indicators['trend_direction'] = self._calculate_trend_direction(close_prices, 50)
            
            # 10. サポート・レジスタンス分析（利用可能な期間で計算）
            lookback = min(data_length, 200)
            support_levels, resistance_levels = self._calculate_support_resistance(close_prices, lookback)
            indicators['support_levels'] = support_levels
            indicators['resistance_levels'] = resistance_levels
            
            # 11. 長期出来高分析（利用可能な期間で計算）
            if data_length >= 50:
                indicators['volume_sma_50'] = self._calculate_sma(volumes, 50)
                indicators['volume_ratio_50'] = self._calculate_volume_ratio(volumes, 50)
            
            # 最新値のみを返す
            latest_indicators = {}
            for key, values in indicators.items():
                try:
                    if values is not None:
                        # デバッグ情報
                        logger.debug(f"処理中: {key}, 型: {type(values)}, 値: {values}")
                        
                        if hasattr(values, 'iloc'):
                            # pandas Seriesの場合
                            if len(values) > 0:
                                latest_value = values.iloc[-1]
                                # NaNチェックと型変換
                                if pd.isna(latest_value):
                                    latest_indicators[key] = None
                                else:
                                    latest_indicators[key] = float(latest_value) if isinstance(latest_value, (int, float, np.number)) else latest_value
                            else:
                                latest_indicators[key] = None
                        elif isinstance(values, (list, tuple)):
                            # リストまたはタプルの場合
                            if len(values) > 0:
                                latest_value = values[-1]
                                # NaNチェックと型変換
                                if pd.isna(latest_value):
                                    latest_indicators[key] = None
                                else:
                                    latest_indicators[key] = float(latest_value) if isinstance(latest_value, (int, float, np.number)) else latest_value
                            else:
                                latest_indicators[key] = None
                        elif isinstance(values, (int, float, str, bool, np.number)):
                            # スカラー値の場合
                            if pd.isna(values):
                                latest_indicators[key] = None
                            else:
                                latest_indicators[key] = float(values) if isinstance(values, (int, float, np.number)) else values
                        else:
                            # その他の型
                            latest_indicators[key] = values
                    else:
                        latest_indicators[key] = None
                except Exception as e:
                    logger.warning(f"指標 {key} の処理中にエラー: {e}")
                    latest_indicators[key] = None
            
            return latest_indicators
            
        except Exception as e:
            logger.error(f"長期テクニカル指標計算中にエラー: {e}")
            return {}
    
    def _calculate_limited_indicators(self, close_prices: pd.Series, high_prices: pd.Series, 
                                    low_prices: pd.Series, volumes: pd.Series, data_length: int) -> Dict:
        """データ不足時の限定的な指標計算"""
        indicators = {}
        
        try:
            # 利用可能な期間で基本指標を計算
            if data_length >= 20:
                indicators['sma_20'] = self._calculate_sma(close_prices, 20)
                indicators['ema_20'] = self._calculate_ema(close_prices, 20)
                indicators['rsi_14'] = self._calculate_rsi(close_prices, 14)
                
                # 短期ボリンジャーバンド
                bb_upper_20, bb_middle_20, bb_lower_20 = self._calculate_bollinger_bands(close_prices, 20)
                indicators['bb_upper_20'] = bb_upper_20
                indicators['bb_middle_20'] = bb_middle_20
                indicators['bb_lower_20'] = bb_lower_20
            
            if data_length >= 14:
                # 短期ストキャスティクス
                stoch_k_14, stoch_d_14 = self._calculate_stochastic(high_prices, low_prices, close_prices, 14, 3)
                indicators['stoch_k_14'] = stoch_k_14
                indicators['stoch_d_14'] = stoch_d_14
            
            # 価格変動率（利用可能な期間で計算）
            if data_length >= 5:
                indicators['price_change_5d'] = self._calculate_price_change(close_prices, 5)
            if data_length >= 10:
                indicators['price_change_10d'] = self._calculate_price_change(close_prices, 10)
            if data_length >= 20:
                indicators['price_change_20d'] = self._calculate_price_change(close_prices, 20)
            
            # トレンド分析（利用可能な期間で計算）
            if data_length >= 20:
                indicators['trend_strength'] = self._calculate_trend_strength(close_prices, 20)
                indicators['trend_direction'] = self._calculate_trend_direction(close_prices, 20)
            
            # サポート・レジスタンス分析
            lookback = min(data_length, 50)
            support_levels, resistance_levels = self._calculate_support_resistance(close_prices, lookback)
            indicators['support_levels'] = support_levels
            indicators['resistance_levels'] = resistance_levels
            
            # 最新値のみを返す
            latest_indicators = {}
            for key, values in indicators.items():
                try:
                    if values is not None:
                        if hasattr(values, 'iloc'):
                            # pandas Seriesの場合
                            if len(values) > 0:
                                latest_indicators[key] = values.iloc[-1]
                            else:
                                latest_indicators[key] = None
                        elif isinstance(values, (list, tuple)):
                            # リストまたはタプルの場合
                            if len(values) > 0:
                                latest_indicators[key] = values[-1]
                            else:
                                latest_indicators[key] = None
                        elif isinstance(values, (int, float, str, bool)):
                            # スカラー値の場合
                            latest_indicators[key] = values
                        else:
                            # その他の型
                            latest_indicators[key] = values
                    else:
                        latest_indicators[key] = None
                except Exception as e:
                    logger.warning(f"限定的指標 {key} の処理中にエラー: {e}")
                    latest_indicators[key] = None
            
            return latest_indicators
            
        except Exception as e:
            logger.error(f"限定的指標計算中にエラー: {e}")
            return {}
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """単純移動平均を計算"""
        return prices.rolling(window=period).mean()
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """指数移動平均を計算"""
        return prices.ewm(span=period).mean()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSIを計算"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd_long_term(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """長期MACDを計算（26週、12週）"""
        ema_12 = prices.ewm(span=12).mean()  # 12週EMA
        ema_26 = prices.ewm(span=26).mean()  # 26週EMA
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
    
    def _calculate_trend_strength(self, prices: pd.Series, period: int) -> float:
        """トレンドの強さを計算（ADX風）"""
        if len(prices) < period:
            return 0.0
        
        # 簡易的なトレンド強度計算
        sma_short = prices.rolling(window=20).mean()
        sma_long = prices.rolling(window=period).mean()
        
        # NaN値を除外して有効なデータを確認
        sma_short_valid = sma_short.dropna()
        sma_long_valid = sma_long.dropna()
        
        if len(sma_short_valid) > 0 and len(sma_long_valid) > 0:
            trend_strength = abs((sma_short_valid.iloc[-1] - sma_long_valid.iloc[-1]) / sma_long_valid.iloc[-1]) * 100
            return min(trend_strength, 100)  # 最大100%に制限
        return 0.0
    
    def _calculate_trend_direction(self, prices: pd.Series, period: int) -> str:
        """トレンド方向を判定"""
        if len(prices) < period:
            return "不明"
        
        sma_short = prices.rolling(window=20).mean()
        sma_long = prices.rolling(window=period).mean()
        
        # NaN値を除外して有効なデータを確認
        sma_short_valid = sma_short.dropna()
        sma_long_valid = sma_long.dropna()
        
        if len(sma_short_valid) > 0 and len(sma_long_valid) > 0:
            if sma_short_valid.iloc[-1] > sma_long_valid.iloc[-1]:
                return "上昇トレンド"
            elif sma_short_valid.iloc[-1] < sma_long_valid.iloc[-1]:
                return "下降トレンド"
            else:
                return "横ばい"
        return "不明"
    
    def _calculate_support_resistance(self, prices: pd.Series, lookback: int) -> Tuple[List[float], List[float]]:
        """サポート・レジスタンスレベルを計算"""
        if len(prices) < lookback:
            return [], []
        
        recent_prices = prices.tail(lookback)
        
        # 簡易的なサポート・レジスタンス計算
        support_levels = [
            float(recent_prices.min()),
            float(recent_prices.quantile(0.25)),
            float(recent_prices.quantile(0.33))
        ]
        
        resistance_levels = [
            float(recent_prices.max()),
            float(recent_prices.quantile(0.75)),
            float(recent_prices.quantile(0.67))
        ]
        
        return support_levels, resistance_levels
    
    def generate_long_term_signals(self, indicators: Dict, current_price: float) -> Dict:
        """長期トレードシグナルを生成"""
        signals = {}
        
        try:
            # ゴールデンクロス/デッドクロス判定
            sma_50 = indicators.get('sma_50')
            sma_200 = indicators.get('sma_200')
            if sma_50 is not None and sma_200 is not None:
                if sma_50 > sma_200:
                    signals['trend_signal'] = 'ゴールデンクロス（強気）'
                else:
                    signals['trend_signal'] = 'デッドクロス（弱気）'
            elif indicators.get('sma_20') is not None and indicators.get('sma_50') is not None:
                # 短期移動平均で代替判定
                if indicators['sma_20'] > indicators['sma_50']:
                    signals['trend_signal'] = '短期ゴールデンクロス（強気）'
                else:
                    signals['trend_signal'] = '短期デッドクロス（弱気）'
            else:
                signals['trend_signal'] = 'トレンド判定不可'
            
            # RSIシグナル判定
            rsi_26 = indicators.get('rsi_26')
            if rsi_26 is not None:
                if rsi_26 > 70:
                    signals['rsi_signal'] = '売られすぎ（強気）'
                elif rsi_26 < 30:
                    signals['rsi_signal'] = '買われすぎ（弱気）'
                else:
                    signals['rsi_signal'] = '中立'
            
            # ボリンジャーバンドシグナル判定
            bb_upper_50 = indicators.get('bb_upper_50')
            bb_lower_50 = indicators.get('bb_lower_50')
            if bb_upper_50 is not None and bb_lower_50 is not None:
                if current_price > bb_upper_50:
                    signals['bb_signal'] = 'バンド上限突破（強気）'
                elif current_price < bb_lower_50:
                    signals['bb_signal'] = 'バンド下限突破（弱気）'
                else:
                    signals['bb_signal'] = 'バンド内（中立）'
            
            # MACDシグナル判定
            macd_line = indicators.get('macd_line_26')
            macd_signal = indicators.get('macd_signal_26')
            if macd_line is not None and macd_signal is not None:
                if macd_line > macd_signal:
                    signals['macd_signal'] = 'MACD強気'
                else:
                    signals['macd_signal'] = 'MACD弱気'
            
            # 総合評価
            bullish_count = 0
            bearish_count = 0
            
            for signal_key, signal_value in signals.items():
                if '強気' in signal_value:
                    bullish_count += 1
                elif '弱気' in signal_value:
                    bearish_count += 1
            
            if bullish_count > bearish_count:
                signals['overall_signal'] = '強気'
            elif bearish_count > bullish_count:
                signals['overall_signal'] = '弱気'
            else:
                signals['overall_signal'] = '中立'
            
            return signals
            
        except Exception as e:
            logger.error(f"長期シグナル生成中にエラー: {e}")
            return {'error': str(e)}
    
    def analyze_long_term_stock(self, price_data: pd.DataFrame, stock_info: Dict) -> Dict:
        """長期株式分析を実行"""
        try:
            # テクニカル指標を計算
            indicators = self.calculate_long_term_indicators(price_data)
            
            # 現在価格を取得
            if price_data is not None and not price_data.empty:
                current_price = price_data['close_price'].iloc[-1]
            else:
                current_price = 0.0
            
            # トレードシグナルを生成
            signals = self.generate_long_term_signals(indicators, current_price)
            
            # 分析結果をまとめる
            analysis_result = {
                'stock_info': stock_info,
                'current_price': current_price,
                'indicators': indicators,
                'signals': signals,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_points': len(price_data) if price_data is not None else 0
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"長期株式分析中にエラー: {e}")
            return {
                'stock_info': stock_info,
                'error': str(e),
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
