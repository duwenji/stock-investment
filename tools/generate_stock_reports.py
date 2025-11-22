#!/usr/bin/env python3
"""
銘柄ごとのレポートを生成し、reportsフォルダに格納するメインスクリプト
portfolio_holdingsとtrading_plansにある銘柄を対象に短期トレード向け分析レポートを生成
"""

import sys
import os
import logging
import json
from datetime import datetime
from typing import Dict
import jinja2
# モジュールのパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from report_generator.data_fetcher import DataFetcher
from report_generator.analyzer import StockAnalyzer
from report_generator.visualizer import StockVisualizer

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('stock_report_generation.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class StockReportGenerator:
    """株式レポート生成クラス"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # コンポーネントの初期化
        self.data_fetcher = DataFetcher()
        self.analyzer = StockAnalyzer()
        self.visualizer = StockVisualizer(self.images_dir)
        
        # Jinja2テンプレート環境の設定
        template_dir = os.path.join(os.path.dirname(__file__), "report_generator")
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=True
        )
    
    def generate_single_report(self, stock_code: str, investment_style: str = None) -> bool:
        """単一銘柄のレポートを生成"""
        try:
            logger.info(f"銘柄 {stock_code} のレポート生成開始（スタイル: {investment_style or '標準'}）")
            
            # 1. データ取得
            stock_data = self.data_fetcher.get_all_stock_data(stock_code)
            
            # DataFrameの空チェックを修正
            price_history = stock_data.get('price_history')
            if price_history is None or (hasattr(price_history, 'empty') and price_history.empty):
                logger.warning(f"銘柄 {stock_code} の株価データがありません")
                return False
            
            # 2. 分析実行（投資スタイル別または標準分析）
            if investment_style:
                analysis_result = self.analyzer.analyze_stock_by_style(stock_data, investment_style)
            else:
                analysis_result = self.analyzer.analyze_stock(stock_data)
                
            if not analysis_result:
                logger.warning(f"銘柄 {stock_code} の分析に失敗しました")
                return False
            
            # 3. 可視化
            charts = self.visualizer.generate_all_charts(stock_data, analysis_result)
            
            # 4. レポート生成
            report_data = self._prepare_report_data(stock_data, analysis_result, charts)
            html_content = self._render_html_template(report_data, investment_style)
            
            # 5. ファイル保存
            if investment_style:
                style_dir = os.path.join(self.output_dir, investment_style)
                os.makedirs(style_dir, exist_ok=True)
                report_filename = os.path.join(style_dir, f"{stock_code}.html")
            else:
                report_filename = os.path.join(self.output_dir, f"{stock_code}.html")
                
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"銘柄 {stock_code} のレポートを保存: {report_filename}")
            return True
            
        except Exception as e:
            logger.error(f"銘柄 {stock_code} のレポート生成中にエラー: {e}")
            return False
    
    def _prepare_report_data(self, stock_data: Dict, analysis_result: Dict, charts: Dict) -> Dict:
        """レポート用データを準備"""
        stock_code = stock_data['stock_code']
        basic_info = stock_data.get('basic_info', {})
        indicators = analysis_result.get('indicators', {})
        signals = analysis_result.get('signals', {})
        
        # 基本情報
        report_data = {
            'stock_code': stock_code,
            'stock_name': basic_info.get('stock_name', '不明'),
            'industry': basic_info.get('industry', '不明'),
            'market': basic_info.get('market', '不明'),
            'analysis_date': analysis_result.get('analysis_date', '不明'),
            'current_price': self._format_number(analysis_result.get('current_price')),
            
            # 価格変動
            'price_change_1d': self._format_percentage(indicators.get('price_change_1d')),
            'price_change_5d': self._format_percentage(indicators.get('price_change_5d')),
            'price_change_20d': self._format_percentage(indicators.get('price_change_20d')),
            
            # テクニカル指標
            'sma_5': self._format_number(indicators.get('sma_5')),
            'sma_10': self._format_number(indicators.get('sma_10')),
            'sma_20': self._format_number(indicators.get('sma_20')),
            'sma_50': self._format_number(indicators.get('sma_50')),
            'rsi_14': self._format_number(indicators.get('rsi_14'), 2),
            'stoch_k': self._format_number(indicators.get('stoch_k'), 2),
            'stoch_d': self._format_number(indicators.get('stoch_d'), 2),
            'bb_upper': self._format_number(indicators.get('bb_upper')),
            'bb_lower': self._format_number(indicators.get('bb_lower')),
            'volatility_20d': self._format_percentage(indicators.get('volatility_20d'), 2),
            
            # シグナル
            'rsi_signal': signals.get('rsi_signal', '不明'),
            'rsi_strength': signals.get('rsi_strength', '不明'),
            'macd_signal': signals.get('macd_signal', '不明'),
            'bb_signal': signals.get('bb_signal', '不明'),
            'stoch_signal': signals.get('stoch_signal', '不明'),
            'overall_signal': signals.get('overall_signal', '不明'),
            'buy_count': signals.get('buy_count', 0),
            'sell_count': signals.get('sell_count', 0),
            
            # ポートフォリオ情報
            'portfolio_info': stock_data.get('portfolio_info', []),
            'trading_plans': stock_data.get('trading_plans', []),
            
            # チャートパス（相対パスで指定）
            'price_chart_path': f"images/{charts.get('price_chart', '').split('/')[-1]}" if charts.get('price_chart') else '',
            'technical_chart_path': f"images/{charts.get('technical_chart', '').split('/')[-1]}" if charts.get('technical_chart') else '',
            'signal_summary_path': f"images/{charts.get('signal_summary', '').split('/')[-1]}" if charts.get('signal_summary') else ''
        }
        
        # CSSクラスの設定
        report_data.update(self._get_css_classes(report_data))
        
        # RSIの解釈
        rsi_value = indicators.get('rsi_14')
        if rsi_value is not None:
            if rsi_value > 70:
                report_data['rsi_interpretation'] = '売りゾーン'
            elif rsi_value < 30:
                report_data['rsi_interpretation'] = '買いゾーン'
            else:
                report_data['rsi_interpretation'] = '中立ゾーン'
        else:
            report_data['rsi_interpretation'] = 'データ不足'
        
        return report_data
    
    def _get_css_classes(self, report_data: Dict) -> Dict:
        """CSSクラスを設定"""
        classes = {}
        
        # 総合評価クラス
        overall_signal = report_data.get('overall_signal', '')
        if '買い' in overall_signal:
            classes['overall_signal_class'] = 'signal-buy'
        elif '売り' in overall_signal:
            classes['overall_signal_class'] = 'signal-sell'
        else:
            classes['overall_signal_class'] = 'signal-neutral'
        
        # 価格変動クラス
        for period in ['1d', '5d', '20d']:
            change = report_data.get(f'price_change_{period}', 0)
            if isinstance(change, (int, float)):
                if change > 0:
                    classes[f'price_change_{period}_class'] = 'signal-buy'
                elif change < 0:
                    classes[f'price_change_{period}_class'] = 'signal-sell'
                else:
                    classes[f'price_change_{period}_class'] = 'signal-neutral'
            else:
                classes[f'price_change_{period}_class'] = 'signal-neutral'
        
        # RSIクラス
        rsi = report_data.get('rsi_14')
        if isinstance(rsi, (int, float)):
            if rsi > 70:
                classes['rsi_class'] = 'signal-sell'
            elif rsi < 30:
                classes['rsi_class'] = 'signal-buy'
            else:
                classes['rsi_class'] = 'signal-neutral'
        else:
            classes['rsi_class'] = 'signal-neutral'
        
        # ストキャスティクスクラス
        for indicator in ['stoch_k', 'stoch_d']:
            value = report_data.get(indicator)
            if isinstance(value, (int, float)):
                if value > 80:
                    classes[f'{indicator}_class'] = 'signal-sell'
                elif value < 20:
                    classes[f'{indicator}_class'] = 'signal-buy'
                else:
                    classes[f'{indicator}_class'] = 'signal-neutral'
            else:
                classes[f'{indicator}_class'] = 'signal-neutral'
        
        # シグナルクラス
        for signal in ['rsi_signal', 'macd_signal', 'bb_signal', 'stoch_signal']:
            value = report_data.get(signal, '')
            if '買い' in str(value):
                classes[f'{signal}_class'] = 'signal-buy'
            elif '売り' in str(value):
                classes[f'{signal}_class'] = 'signal-sell'
            else:
                classes[f'{signal}_class'] = 'signal-neutral'
        
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
    
    def _render_html_template(self, report_data: Dict, investment_style: str = None) -> str:
        """HTMLテンプレートをレンダリング"""
        try:
            # 投資スタイルに応じたテンプレートを選択
            if investment_style == 'day_trading':
                template_name = 'day_trading_template.html'
            elif investment_style == 'swing_trading':
                template_name = 'swing_trading_template.html'
            elif investment_style == 'long_term':
                template_name = 'long_term_investment_template.html'
            else:
                template_name = 'template.html'
            
            template = self.template_env.get_template(template_name)
            return template.render(**report_data)
        except Exception as e:
            logger.error(f"HTMLテンプレートのレンダリング中にエラー: {e}")
            return f"<html><body><h1>エラー: テンプレートのレンダリングに失敗しました</h1><p>{e}</p></body></html>"
    
    def generate_all_reports(self) -> Dict:
        """すべての対象銘柄のレポートを生成"""
        logger.info("=== 銘柄レポート生成開始 ===")
        start_time = datetime.now()
        
        try:
            # 対象銘柄の取得
            target_stocks = self.data_fetcher.get_target_stock_codes()
            if not target_stocks:
                logger.error("対象銘柄が見つかりません")
                return {'success': False, 'message': '対象銘柄が見つかりません'}
            
            logger.info(f"対象銘柄数: {len(target_stocks)}")
            
            # 各銘柄のレポート生成
            success_count = 0
            failed_stocks = []
            
            for stock_code in target_stocks:
                if self.generate_single_report(stock_code):
                    success_count += 1
                else:
                    failed_stocks.append(stock_code)
            
            # 実行結果のサマリー
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            summary = {
                'success': True,
                'total_stocks': len(target_stocks),
                'success_count': success_count,
                'failed_count': len(failed_stocks),
                'failed_stocks': failed_stocks,
                'execution_time': execution_time,
                'output_dir': self.output_dir
            }
            
            logger.info("=== 銘柄レポート生成完了 ===")
            logger.info(f"実行時間: {execution_time:.2f}秒")
            logger.info(f"総銘柄数: {len(target_stocks)}")
            logger.info(f"レポート生成成功: {success_count}銘柄")
            logger.info(f"レポート生成失敗: {len(failed_stocks)}銘柄")
            
            if failed_stocks:
                logger.info(f"失敗銘柄詳細: {failed_stocks}")
            
            # サマリーファイルを保存
            summary_file = os.path.join(self.output_dir, "generation_summary.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"サマリーファイルを保存: {summary_file}")
            
            return summary
            
        except Exception as e:
            logger.error(f"レポート生成中にエラー: {e}")
            return {'success': False, 'message': str(e)}

def main():
    """メイン処理"""
    try:
        # レポート生成器の初期化
        generator = StockReportGenerator()
        
        # すべてのレポートを生成
        result = generator.generate_all_reports()
        
        if result['success']:
            print(f"\n✅ レポート生成完了")
            print(f"   対象銘柄数: {result['total_stocks']}")
            print(f"   成功: {result['success_count']}銘柄")
            print(f"   失敗: {result['failed_count']}銘柄")
            print(f"   実行時間: {result['execution_time']:.2f}秒")
            print(f"   出力先: {result['output_dir']}")
            
            if result['failed_stocks']:
                print(f"   失敗銘柄: {', '.join(result['failed_stocks'])}")
        else:
            print(f"\n❌ レポート生成失敗: {result['message']}")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"メイン処理中にエラー: {e}")
        print(f"\n❌ エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
