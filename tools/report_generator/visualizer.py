#!/usr/bin/env python3
"""
銘柄レポート生成用可視化モジュール
価格チャートとテクニカル指標のグラフを生成
"""

import logging
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import io
import base64

# 日本語フォント設定
plt.rcParams['font.family'] = ['MS Gothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

class StockVisualizer:
    """株式可視化クラス"""
    
    def __init__(self, output_dir: str = "reports/images"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_price_chart(self, stock_data: Dict, analysis_result: Dict) -> Optional[str]:
        """価格チャートを作成"""
        try:
            price_history = stock_data['price_history']
            if price_history is None or price_history.empty:
                return None
            
            stock_code = stock_data['stock_code']
            basic_info = stock_data['basic_info']
            stock_name = basic_info.get('stock_name', stock_code) if basic_info else stock_code
            
            # チャート作成
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # 価格チャート
            dates = price_history['price_date']
            close_prices = price_history['close_price']
            
            # 移動平均を計算
            sma_20 = close_prices.rolling(window=20).mean()
            sma_50 = close_prices.rolling(window=50).mean()
            
            # 価格と移動平均をプロット
            ax1.plot(dates, close_prices, label='終値', color='black', linewidth=1)
            ax1.plot(dates, sma_20, label='20日移動平均', color='blue', linewidth=1, alpha=0.7)
            ax1.plot(dates, sma_50, label='50日移動平均', color='red', linewidth=1, alpha=0.7)
            
            # 現在価格を強調表示
            current_price = analysis_result.get('current_price')
            if current_price:
                latest_date = dates.iloc[-1]
                ax1.scatter(latest_date, current_price, color='red', s=50, zorder=5)
                ax1.annotate(f'現在: {current_price:.0f}円', 
                           (latest_date, current_price),
                           xytext=(10, 10), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
            
            ax1.set_title(f'{stock_name} ({stock_code}) - 価格チャート', fontsize=14, fontweight='bold')
            ax1.set_ylabel('価格 (円)', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 日付フォーマット
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax1.xaxis.set_major_locator(mdates.MonthLocator())
            
            # 出来高チャート
            volumes = price_history['volume']
            ax2.bar(dates, volumes, color='lightblue', alpha=0.7)
            ax2.set_ylabel('出来高', fontsize=12)
            ax2.set_xlabel('日付', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # 日付フォーマット
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax2.xaxis.set_major_locator(mdates.MonthLocator())
            
            plt.tight_layout()
            
            # 画像を保存
            filename = f"{self.output_dir}/{stock_code}_price_chart.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"価格チャートを保存: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"価格チャート作成中にエラー: {e}")
            return None
    
    def create_technical_chart(self, stock_data: Dict, analysis_result: Dict) -> Optional[str]:
        """テクニカル指標チャートを作成"""
        try:
            price_history = stock_data['price_history']
            if price_history is None or price_history.empty:
                return None
            
            stock_code = stock_data['stock_code']
            basic_info = stock_data['basic_info']
            stock_name = basic_info.get('stock_name', stock_code) if basic_info else stock_code
            
            # 4つのサブプロットを作成
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            dates = price_history['price_date']
            close_prices = price_history['close_price']
            high_prices = price_history['high_price']
            low_prices = price_history['low_price']
            volumes = price_history['volume']
            
            # 1. RSIチャート
            rsi = self._calculate_rsi(close_prices, 14)
            ax1.plot(dates, rsi, label='RSI(14)', color='purple', linewidth=1)
            ax1.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='売りゾーン')
            ax1.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='買いゾーン')
            ax1.axhline(y=50, color='gray', linestyle='-', alpha=0.5)
            ax1.set_ylabel('RSI', fontsize=10)
            ax1.set_ylim(0, 100)
            ax1.legend(fontsize=8)
            ax1.grid(True, alpha=0.3)
            ax1.set_title('RSI指標', fontsize=12)
            
            # 2. MACDチャート
            macd_line, macd_signal, macd_histogram = self._calculate_macd(close_prices)
            ax2.plot(dates, macd_line, label='MACD', color='blue', linewidth=1)
            ax2.plot(dates, macd_signal, label='シグナル', color='red', linewidth=1)
            ax2.bar(dates, macd_histogram, label='ヒストグラム', color='gray', alpha=0.5)
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax2.set_ylabel('MACD', fontsize=10)
            ax2.legend(fontsize=8)
            ax2.grid(True, alpha=0.3)
            ax2.set_title('MACD指標', fontsize=12)
            
            # 3. ボリンジャーバンド
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close_prices, 20)
            ax3.plot(dates, close_prices, label='終値', color='black', linewidth=1)
            ax3.plot(dates, bb_upper, label='上限', color='red', linewidth=1, alpha=0.7)
            ax3.plot(dates, bb_middle, label='中央', color='blue', linewidth=1, alpha=0.7)
            ax3.plot(dates, bb_lower, label='下限', color='green', linewidth=1, alpha=0.7)
            ax3.fill_between(dates, bb_upper, bb_lower, alpha=0.1, color='gray')
            ax3.set_ylabel('価格 (円)', fontsize=10)
            ax3.legend(fontsize=8)
            ax3.grid(True, alpha=0.3)
            ax3.set_title('ボリンジャーバンド', fontsize=12)
            
            # 4. ストキャスティクス
            stoch_k, stoch_d = self._calculate_stochastic(high_prices, low_prices, close_prices, 14, 3)
            ax4.plot(dates, stoch_k, label='%K', color='blue', linewidth=1)
            ax4.plot(dates, stoch_d, label='%D', color='red', linewidth=1)
            ax4.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='売りゾーン')
            ax4.axhline(y=20, color='green', linestyle='--', alpha=0.7, label='買いゾーン')
            ax4.set_ylabel('ストキャスティクス', fontsize=10)
            ax4.set_ylim(0, 100)
            ax4.legend(fontsize=8)
            ax4.grid(True, alpha=0.3)
            ax4.set_title('ストキャスティクス', fontsize=12)
            
            # 日付フォーマット
            for ax in [ax1, ax2, ax3, ax4]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax.xaxis.set_major_locator(mdates.MonthLocator())
            
            plt.suptitle(f'{stock_name} ({stock_code}) - テクニカル指標', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # 画像を保存
            filename = f"{self.output_dir}/{stock_code}_technical_chart.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"テクニカルチャートを保存: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"テクニカルチャート作成中にエラー: {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSIを計算"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series) -> tuple:
        """MACDを計算"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        macd_signal = macd_line.ewm(span=9).mean()
        macd_histogram = macd_line - macd_signal
        return macd_line, macd_signal, macd_histogram
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> tuple:
        """ボリンジャーバンドを計算"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        bb_upper = sma + (std * 2)
        bb_lower = sma - (std * 2)
        return bb_upper, sma, bb_lower
    
    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                            k_period: int = 14, d_period: int = 3) -> tuple:
        """ストキャスティクスを計算"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        stoch_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        stoch_d = stoch_k.rolling(window=d_period).mean()
        return stoch_k, stoch_d
    
    def create_signal_summary_chart(self, analysis_result: Dict) -> Optional[str]:
        """シグナルサマリーチャートを作成"""
        try:
            stock_code = analysis_result['stock_code']
            signals = analysis_result.get('signals', {})
            
            if not signals:
                return None
            
            # シグナルをカテゴリ別に分類
            signal_types = ['買い', '売り', '中立']
            signal_counts = {
                '買い': signals.get('buy_count', 0),
                '売り': signals.get('sell_count', 0),
                '中立': len([v for v in signals.values() if v == '中立'])
            }
            
            # 円グラフを作成
            fig, ax = plt.subplots(figsize=(8, 6))
            
            colors = ['green', 'red', 'gray']
            explode = (0.1, 0.1, 0)  # 買いと売りを強調
            
            wedges, texts, autotexts = ax.pie(
                [signal_counts[t] for t in signal_types],
                explode=explode,
                labels=signal_types,
                colors=colors,
                autopct='%1.1f%%',
                startangle=90
            )
            
            # テキストのスタイルを設定
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title(f'{stock_code} - トレードシグナル分布', fontsize=14, fontweight='bold')
            
            # 総合評価を追加
            overall_signal = signals.get('overall_signal', '不明')
            plt.figtext(0.5, 0.01, f'総合評価: {overall_signal}', 
                       ha='center', fontsize=12, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))
            
            # 画像を保存
            filename = f"{self.output_dir}/{stock_code}_signal_summary.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"シグナルサマリーチャートを保存: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"シグナルサマリーチャート作成中にエラー: {e}")
            return None
    
    def generate_all_charts(self, stock_data: Dict, analysis_result: Dict) -> Dict:
        """すべてのチャートを生成"""
        try:
            stock_code = stock_data['stock_code']
            
            charts = {
                'price_chart': self.create_price_chart(stock_data, analysis_result),
                'technical_chart': self.create_technical_chart(stock_data, analysis_result),
                'signal_summary': self.create_signal_summary_chart(analysis_result)
            }
            
            # None値を除去
            charts = {k: v for k, v in charts.items() if v is not None}
            
            logger.info(f"銘柄 {stock_code} のチャート生成完了: {len(charts)}個")
            return charts
            
        except Exception as e:
            logger.error(f"チャート生成中にエラー: {e}")
            return {}
