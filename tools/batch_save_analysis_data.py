#!/usr/bin/env python3
"""
分析データのバッチ保存スクリプト
レポート生成後に分析結果をデータベースに一括保存
"""

import sys
import os
import logging
import json
from datetime import datetime, date
from typing import Dict, List

# モジュールのパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 直接インポート
from report_generator.data_fetcher import DataFetcher
from report_generator.analyzer import StockAnalyzer
from report_generator.database_manager import AnalysisDataManager

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('batch_save_analysis.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class BatchDataSaver:
    """分析データバッチ保存クラス"""
    
    def __init__(self, database_url: str = None):
        self.data_fetcher = DataFetcher()
        self.analyzer = StockAnalyzer()
        self.data_manager = AnalysisDataManager(database_url)
    
    def save_all_analysis_data(self, investment_styles: List[str] = None) -> Dict:
        """すべての対象銘柄の分析データを保存"""
        logger.info("=== 分析データバッチ保存開始 ===")
        start_time = datetime.now()
        
        try:
            # 対象銘柄の取得
            target_stocks = self.data_fetcher.get_target_stock_codes()
            if not target_stocks:
                logger.error("対象銘柄が見つかりません")
                return {'success': False, 'message': '対象銘柄が見つかりません'}
            
            logger.info(f"対象銘柄数: {len(target_stocks)}")
            
            # 投資スタイルの設定
            if investment_styles is None:
                investment_styles = ['short_term', 'long_term']
            
            # 各銘柄の分析データを保存
            total_success = 0
            total_failed = 0
            failed_stocks = []
            
            for stock_code in target_stocks:
                logger.info(f"銘柄 {stock_code} の分析データ保存開始")
                
                stock_success = True
                for style in investment_styles:
                    try:
                        # データ取得
                        stock_data = self.data_fetcher.get_all_stock_data(stock_code)
                        
                        # 分析実行
                        analysis_result = self.analyzer.analyze_stock_by_style(stock_data, style)
                        
                        if not analysis_result:
                            logger.warning(f"銘柄 {stock_code} の分析に失敗しました（スタイル: {style}）")
                            stock_success = False
                            continue
                        
                        # データベース保存
                        indicators_saved = self._save_technical_indicators(
                            stock_code, analysis_result, style
                        )
                        
                        decision_saved = self._save_investment_decision(
                            stock_code, analysis_result, style
                        )
                        
                        if indicators_saved and decision_saved:
                            logger.info(f"銘柄 {stock_code} の分析データを保存しました（スタイル: {style}）")
                        else:
                            logger.warning(f"銘柄 {stock_code} の一部データ保存に失敗しました（スタイル: {style}）")
                            stock_success = False
                            
                    except Exception as e:
                        logger.error(f"銘柄 {stock_code} の分析データ保存中にエラー（スタイル: {style}）: {e}")
                        stock_success = False
                
                if stock_success:
                    total_success += 1
                else:
                    total_failed += 1
                    failed_stocks.append(stock_code)
            
            # 実行結果のサマリー
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            summary = {
                'success': True,
                'total_stocks': len(target_stocks),
                'success_count': total_success,
                'failed_count': total_failed,
                'failed_stocks': failed_stocks,
                'execution_time': execution_time,
                'investment_styles': investment_styles
            }
            
            logger.info("=== 分析データバッチ保存完了 ===")
            logger.info(f"実行時間: {execution_time:.2f}秒")
            logger.info(f"総銘柄数: {len(target_stocks)}")
            logger.info(f"保存成功: {total_success}銘柄")
            logger.info(f"保存失敗: {total_failed}銘柄")
            
            if failed_stocks:
                logger.info(f"失敗銘柄詳細: {failed_stocks}")
            
            # サマリーファイルを保存
            summary_file = "batch_save_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"サマリーファイルを保存: {summary_file}")
            
            return summary
            
        except Exception as e:
            logger.error(f"バッチ保存中にエラー: {e}")
            return {'success': False, 'message': str(e)}
    
    def _save_technical_indicators(self, stock_code: str, analysis_result: Dict, 
                                 investment_style: str) -> bool:
        """テクニカル指標を保存"""
        try:
            indicators = analysis_result.get('indicators', {})
            return self.data_manager.save_technical_indicators(
                stock_code, indicators, investment_style
            )
        except Exception as e:
            logger.error(f"テクニカル指標保存中にエラー（銘柄: {stock_code}, スタイル: {investment_style}）: {e}")
            return False
    
    def _save_investment_decision(self, stock_code: str, analysis_result: Dict, 
                                investment_style: str) -> bool:
        """投資判断を保存"""
        try:
            signals = analysis_result.get('signals', {})
            decision_data = {
                'decision_type': 'analyze',
                'target_price': analysis_result.get('target_price'),
                'stop_loss': analysis_result.get('stop_loss'),
                'confidence_score': analysis_result.get('confidence_score'),
                'rsi_signal': signals.get('rsi_signal'),
                'macd_signal': signals.get('macd_signal'),
                'bb_signal': signals.get('bb_signal'),
                'stoch_signal': signals.get('stoch_signal'),
                'overall_signal': signals.get('overall_signal'),
                'buy_count': signals.get('buy_count'),
                'sell_count': signals.get('sell_count'),
                'ai_reasoning': analysis_result.get('ai_reasoning'),
                'risk_assessment': analysis_result.get('risk_assessment')
            }
            
            return self.data_manager.save_investment_decision(
                stock_code, decision_data, investment_style
            )
        except Exception as e:
            logger.error(f"投資判断保存中にエラー（銘柄: {stock_code}, スタイル: {investment_style}）: {e}")
            return False
    
    def save_single_stock_data(self, stock_code: str, investment_styles: List[str] = None) -> Dict:
        """単一銘柄の分析データを保存"""
        try:
            if investment_styles is None:
                investment_styles = ['short_term', 'long_term']
            
            logger.info(f"銘柄 {stock_code} の分析データ保存開始")
            
            # データ取得
            stock_data = self.data_fetcher.get_all_stock_data(stock_code)
            
            if not stock_data:
                return {'success': False, 'message': f'銘柄 {stock_code} のデータ取得に失敗'}
            
            results = {}
            for style in investment_styles:
                try:
                    # 分析実行
                    analysis_result = self.analyzer.analyze_stock_by_style(stock_data, style)
                    
                    if not analysis_result:
                        results[style] = {'success': False, 'message': '分析失敗'}
                        continue
                    
                    # データベース保存
                    indicators_saved = self._save_technical_indicators(stock_code, analysis_result, style)
                    decision_saved = self._save_investment_decision(stock_code, analysis_result, style)
                    
                    if indicators_saved and decision_saved:
                        results[style] = {'success': True, 'message': '保存成功'}
                    else:
                        results[style] = {'success': False, 'message': '一部保存失敗'}
                        
                except Exception as e:
                    results[style] = {'success': False, 'message': str(e)}
            
            # 結果の集計
            success_count = sum(1 for result in results.values() if result.get('success', False))
            total_count = len(results)
            
            summary = {
                'success': success_count > 0,
                'stock_code': stock_code,
                'total_styles': total_count,
                'success_styles': success_count,
                'failed_styles': total_count - success_count,
                'results': results
            }
            
            logger.info(f"銘柄 {stock_code} の分析データ保存完了: {success_count}/{total_count} スタイル成功")
            
            return summary
            
        except Exception as e:
            logger.error(f"単一銘柄保存中にエラー: {e}")
            return {'success': False, 'message': str(e)}

def main():
    """メイン処理"""
    try:
        print("=== 分析データバッチ保存システム ===")
        
        # バッチ保存器の初期化
        saver = BatchDataSaver()
        
        # すべての分析データを保存
        result = saver.save_all_analysis_data()
        
        if result['success']:
            print(f"\n✅ 分析データ保存完了")
            print(f"   対象銘柄数: {result['total_stocks']}")
            print(f"   保存成功: {result['success_count']}銘柄")
            print(f"   保存失敗: {result['failed_count']}銘柄")
            print(f"   実行時間: {result['execution_time']:.2f}秒")
            print(f"   投資スタイル: {', '.join(result['investment_styles'])}")
            
            if result['failed_stocks']:
                print(f"   失敗銘柄: {', '.join(result['failed_stocks'])}")
        else:
            print(f"\n❌ 分析データ保存失敗: {result['message']}")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"メイン処理中にエラー: {e}")
        print(f"\n❌ エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
