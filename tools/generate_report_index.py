#!/usr/bin/env python3
"""
銘柄レポート一覧ページを生成するスクリプト
短期・長期レポートの両方を対象とした一覧ページを作成
"""

import sys
import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Optional
import jinja2

# モジュールのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from report_generator.data_fetcher import DataFetcher
from report_generator.analyzer import StockAnalyzer
from report_generator.long_term_analyzer import LongTermStockAnalyzer

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('report_index_generation.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ReportIndexGenerator:
    """レポート一覧ページ生成クラス"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        self.short_term_dir = os.path.join(output_dir, "short_term")
        self.long_term_dir = os.path.join(output_dir, "long_term")
        
        # コンポーネントの初期化
        self.data_fetcher = DataFetcher()
        self.short_term_analyzer = StockAnalyzer()
        self.long_term_analyzer = LongTermStockAnalyzer()
        
        # Jinja2テンプレート環境の設定
        template_dir = os.path.join(os.path.dirname(__file__), "report_generator")
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=True
        )
    
    def get_stock_summary_data(self, stock_code: str) -> Optional[Dict]:
        """銘柄のサマリーデータを取得"""
        try:
            # データ取得
            stock_data = self.data_fetcher.get_all_stock_data(stock_code)
            
            # 基本情報
            basic_info = stock_data.get('basic_info', {})
            price_history = stock_data.get('price_history')
            
            if price_history is None or (hasattr(price_history, 'empty') and price_history.empty):
                logger.warning(f"銘柄 {stock_code} の株価データがありません")
                return None
            
            # 現在価格
            current_price = price_history['close_price'].iloc[-1] if len(price_history) > 0 else None
            
            # 短期分析
            short_term_analysis = self.short_term_analyzer.analyze_stock(stock_data)
            short_term_signals = short_term_analysis.get('signals', {}) if short_term_analysis else {}
            
            # 長期分析（データが十分な場合のみ）
            long_term_analysis = None
            long_term_signals = {}
            if len(price_history) >= 200:
                # stock_infoを準備
                stock_info = {
                    'stock_code': stock_code,
                    'stock_name': basic_info.get('stock_name', '不明'),
                    'industry': basic_info.get('industry', '不明'),
                    'market': basic_info.get('market', '不明')
                }
                long_term_analysis = self.long_term_analyzer.analyze_long_term_stock(price_history, stock_info)
                long_term_signals = long_term_analysis.get('signals', {}) if long_term_analysis else {}
            
            # 価格変動計算
            price_change_1d = self._calculate_price_change(price_history, 1)
            price_change_5d = self._calculate_price_change(price_history, 5)
            price_change_20d = self._calculate_price_change(price_history, 20)
            
            summary_data = {
                'stock_code': stock_code,
                'stock_name': basic_info.get('stock_name', '不明'),
                'industry': basic_info.get('industry', '不明'),
                'market': basic_info.get('market', '不明'),
                'current_price': current_price,
                'price_change_1d': price_change_1d,
                'price_change_5d': price_change_5d,
                'price_change_20d': price_change_20d,
                'short_term_signal': short_term_signals.get('overall_signal', '不明'),
                'long_term_signal': long_term_signals.get('overall_signal', '不明'),
                'short_term_buy_count': short_term_signals.get('buy_count', 0),
                'short_term_sell_count': short_term_signals.get('sell_count', 0),
                'long_term_buy_count': long_term_signals.get('buy_count', 0),
                'long_term_sell_count': long_term_signals.get('sell_count', 0),
                'has_long_term_analysis': long_term_analysis is not None,
                'data_points': len(price_history)
            }
            
            # CSSクラスの設定
            summary_data.update(self._get_summary_css_classes(summary_data))
            
            return summary_data
            
        except Exception as e:
            logger.error(f"銘柄 {stock_code} のサマリーデータ取得中にエラー: {e}")
            return None
    
    def _calculate_price_change(self, price_history, period: int) -> Optional[float]:
        """価格変動率を計算"""
        try:
            if len(price_history) < period + 1:
                return None
            
            current_price = price_history['close_price'].iloc[-1]
            past_price = price_history['close_price'].iloc[-period-1]
            
            if past_price == 0:
                return None
            
            return ((current_price - past_price) / past_price) * 100
        except Exception:
            return None
    
    def _get_summary_css_classes(self, summary_data: Dict) -> Dict:
        """サマリーデータ用CSSクラスを設定"""
        classes = {}
        
        # 短期シグナルクラス
        short_term_signal = summary_data.get('short_term_signal', '')
        if '買い' in short_term_signal:
            classes['short_term_signal_class'] = 'signal-buy'
        elif '売り' in short_term_signal:
            classes['short_term_signal_class'] = 'signal-sell'
        else:
            classes['short_term_signal_class'] = 'signal-neutral'
        
        # 長期シグナルクラス
        long_term_signal = summary_data.get('long_term_signal', '')
        if '買い' in long_term_signal:
            classes['long_term_signal_class'] = 'signal-buy'
        elif '売り' in long_term_signal:
            classes['long_term_signal_class'] = 'signal-sell'
        else:
            classes['long_term_signal_class'] = 'signal-neutral'
        
        # 価格変動クラス
        for period in ['1d', '5d', '20d']:
            change = summary_data.get(f'price_change_{period}')
            if change is not None:
                if change > 0:
                    classes[f'price_change_{period}_class'] = 'signal-buy'
                elif change < 0:
                    classes[f'price_change_{period}_class'] = 'signal-sell'
                else:
                    classes[f'price_change_{period}_class'] = 'signal-neutral'
            else:
                classes[f'price_change_{period}_class'] = 'signal-neutral'
        
        return classes
    
    def _format_number(self, value, decimals: int = 0) -> str:
        """数値をフォーマット"""
        if value is None:
            return '不明'
        try:
            if decimals == 0:
                return f"{int(value):,}"
            else:
                return f"{float(value):.{decimals}f}"
        except (ValueError, TypeError):
            return '不明'
    
    def _format_percentage(self, value, decimals: int = 2) -> str:
        """パーセンテージをフォーマット"""
        if value is None:
            return '不明'
        try:
            return f"{float(value):.{decimals}f}%"
        except (ValueError, TypeError):
            return '不明'
    
    def _render_html_template(self, index_data: Dict) -> str:
        """HTMLテンプレートをレンダリング"""
        try:
            template = self.template_env.get_template('index_template.html')
            return template.render(**index_data)
        except Exception as e:
            logger.error(f"HTMLテンプレートのレンダリング中にエラー: {e}")
            return f"<html><body><h1>エラー: テンプレートのレンダリングに失敗しました</h1><p>{e}</p></body></html>"
    
    def generate_index_page(self) -> Dict:
        """一覧ページを生成"""
        logger.info("=== レポート一覧ページ生成開始 ===")
        start_time = datetime.now()
        
        try:
            # 対象銘柄の取得
            target_stocks = self.data_fetcher.get_target_stock_codes()
            if not target_stocks:
                logger.error("対象銘柄が見つかりません")
                return {'success': False, 'message': '対象銘柄が見つかりません'}
            
            logger.info(f"対象銘柄数: {len(target_stocks)}")
            
            # 各銘柄のサマリーデータを収集
            stock_summaries = []
            failed_stocks = []
            
            for stock_code in target_stocks:
                summary_data = self.get_stock_summary_data(stock_code)
                if summary_data:
                    # 数値フォーマット
                    summary_data['current_price_formatted'] = self._format_number(summary_data['current_price'])
                    summary_data['price_change_1d_formatted'] = self._format_percentage(summary_data['price_change_1d'])
                    summary_data['price_change_5d_formatted'] = self._format_percentage(summary_data['price_change_5d'])
                    summary_data['price_change_20d_formatted'] = self._format_percentage(summary_data['price_change_20d'])
                    
                    stock_summaries.append(summary_data)
                else:
                    failed_stocks.append(stock_code)
            
            # 統計情報の計算
            total_stocks = len(target_stocks)
            successful_stocks = len(stock_summaries)
            short_term_buy_signals = sum(1 for s in stock_summaries if '買い' in s.get('short_term_signal', ''))
            short_term_sell_signals = sum(1 for s in stock_summaries if '売り' in s.get('short_term_signal', ''))
            long_term_buy_signals = sum(1 for s in stock_summaries if '買い' in s.get('long_term_signal', ''))
            long_term_sell_signals = sum(1 for s in stock_summaries if '売り' in s.get('long_term_signal', ''))
            
            # 一覧ページデータの準備
            index_data = {
                'stock_summaries': stock_summaries,
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_stocks': total_stocks,
                'successful_stocks': successful_stocks,
                'failed_stocks': failed_stocks,
                'short_term_buy_signals': short_term_buy_signals,
                'short_term_sell_signals': short_term_sell_signals,
                'long_term_buy_signals': long_term_buy_signals,
                'long_term_sell_signals': long_term_sell_signals,
                'short_term_neutral_signals': successful_stocks - short_term_buy_signals - short_term_sell_signals,
                'long_term_neutral_signals': successful_stocks - long_term_buy_signals - long_term_sell_signals
            }
            
            # HTMLページを生成
            html_content = self._render_html_template(index_data)
            
            # ファイル保存
            index_filename = os.path.join(self.output_dir, "index.html")
            with open(index_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 実行結果のサマリー
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            summary = {
                'success': True,
                'total_stocks': total_stocks,
                'successful_stocks': successful_stocks,
                'failed_stocks': failed_stocks,
                'execution_time': execution_time,
                'output_file': index_filename
            }
            
            logger.info("=== レポート一覧ページ生成完了 ===")
            logger.info(f"実行時間: {execution_time:.2f}秒")
            logger.info(f"総銘柄数: {total_stocks}")
            logger.info(f"成功: {successful_stocks}銘柄")
            logger.info(f"失敗: {len(failed_stocks)}銘柄")
            logger.info(f"出力ファイル: {index_filename}")
            
            if failed_stocks:
                logger.info(f"失敗銘柄詳細: {failed_stocks}")
            
            return summary
            
        except Exception as e:
            logger.error(f"一覧ページ生成中にエラー: {e}")
            return {'success': False, 'message': str(e)}

def main():
    """メイン処理"""
    try:
        # 一覧ページ生成器の初期化
        generator = ReportIndexGenerator()
        
        # 一覧ページを生成
        result = generator.generate_index_page()
        
        if result['success']:
            print(f"\n✅ 一覧ページ生成完了")
            print(f"   対象銘柄数: {result['total_stocks']}")
            print(f"   成功: {result['successful_stocks']}銘柄")
            print(f"   失敗: {len(result['failed_stocks'])}銘柄")
            print(f"   実行時間: {result['execution_time']:.2f}秒")
            print(f"   出力先: {result['output_file']}")
            
            if result['failed_stocks']:
                print(f"   失敗銘柄: {', '.join(result['failed_stocks'])}")
        else:
            print(f"\n❌ 一覧ページ生成失敗: {result['message']}")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"メイン処理中にエラー: {e}")
        print(f"\n❌ エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
