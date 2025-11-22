#!/usr/bin/env python3
"""
すべてのレポートを一括生成する統合スクリプト
短期レポート、長期レポート、一覧ページを順次生成
"""

import sys
import os
import logging
import json
from datetime import datetime
from typing import Dict

# モジュールのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('all_reports_generation.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class AllReportsGenerator:
    """全レポート一括生成クラス"""
    
    def __init__(self):
        self.output_dir = "reports"
        self.short_term_dir = os.path.join(self.output_dir, "short_term")
        self.long_term_dir = os.path.join(self.output_dir, "long_term")
        
        # 出力ディレクトリの作成
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.short_term_dir, exist_ok=True)
        os.makedirs(self.long_term_dir, exist_ok=True)
    
    def generate_short_term_reports(self) -> Dict:
        """短期レポートを生成"""
        try:
            logger.info("=== 短期レポート生成開始 ===")
            
            # 短期レポート生成スクリプトをインポートして実行
            from generate_stock_reports import StockReportGenerator
            
            generator = StockReportGenerator(output_dir=self.short_term_dir)
            result = generator.generate_all_reports()
            
            logger.info("=== 短期レポート生成完了 ===")
            return result
            
        except Exception as e:
            logger.error(f"短期レポート生成中にエラー: {e}")
            return {'success': False, 'message': str(e)}
    
    def generate_long_term_reports(self) -> Dict:
        """長期レポートを生成"""
        try:
            logger.info("=== 長期レポート生成開始 ===")
            
            # 長期レポート生成スクリプトをインポートして実行
            from generate_long_term_reports import LongTermStockReportGenerator
            
            generator = LongTermStockReportGenerator(output_dir=self.long_term_dir)
            result = generator.generate_all_reports()
            
            logger.info("=== 長期レポート生成完了 ===")
            return result
            
        except Exception as e:
            logger.error(f"長期レポート生成中にエラー: {e}")
            return {'success': False, 'message': str(e)}
    
    def generate_index_page(self) -> Dict:
        """一覧ページを生成"""
        try:
            logger.info("=== 一覧ページ生成開始 ===")
            
            # 一覧ページ生成スクリプトをインポートして実行
            from generate_report_index import ReportIndexGenerator
            
            generator = ReportIndexGenerator(output_dir=self.output_dir)
            result = generator.generate_index_page()
            
            logger.info("=== 一覧ページ生成完了 ===")
            return result
            
        except Exception as e:
            logger.error(f"一覧ページ生成中にエラー: {e}")
            return {'success': False, 'message': str(e)}
    
    def generate_all(self) -> Dict:
        """すべてのレポートを生成"""
        logger.info("=== 全レポート一括生成開始 ===")
        start_time = datetime.now()
        
        try:
            # 1. 短期レポート生成
            short_term_result = self.generate_short_term_reports()
            if not short_term_result.get('success', False):
                logger.error("短期レポート生成に失敗しました")
                return {'success': False, 'message': '短期レポート生成に失敗'}
            
            # 2. 長期レポート生成
            long_term_result = self.generate_long_term_reports()
            if not long_term_result.get('success', False):
                logger.warning("長期レポート生成に失敗しましたが、処理を継続します")
            
            # 3. 一覧ページ生成
            index_result = self.generate_index_page()
            if not index_result.get('success', False):
                logger.error("一覧ページ生成に失敗しました")
                return {'success': False, 'message': '一覧ページ生成に失敗'}
            
            # 実行結果のサマリー
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            summary = {
                'success': True,
                'execution_time': execution_time,
                'short_term': short_term_result,
                'long_term': long_term_result,
                'index': index_result,
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info("=== 全レポート一括生成完了 ===")
            logger.info(f"実行時間: {execution_time:.2f}秒")
            
            # サマリーファイルを保存
            summary_file = os.path.join(self.output_dir, "all_reports_summary.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"サマリーファイルを保存: {summary_file}")
            
            return summary
            
        except Exception as e:
            logger.error(f"全レポート生成中にエラー: {e}")
            return {'success': False, 'message': str(e)}

def main():
    """メイン処理"""
    try:
        # 全レポート生成器の初期化
        generator = AllReportsGenerator()
        
        # すべてのレポートを生成
        result = generator.generate_all()
        
        if result['success']:
            print(f"\n✅ 全レポート生成完了")
            print(f"   実行時間: {result['execution_time']:.2f}秒")
            print(f"   出力先: reports/")
            
            # 短期レポート結果
            short_term = result['short_term']
            print(f"\n📊 短期レポート:")
            print(f"   対象銘柄数: {short_term.get('total_stocks', 0)}")
            print(f"   成功: {short_term.get('success_count', 0)}銘柄")
            print(f"   失敗: {short_term.get('failed_count', 0)}銘柄")
            
            # 長期レポート結果
            long_term = result['long_term']
            if long_term.get('success', False):
                print(f"\n📈 長期レポート:")
                print(f"   対象銘柄数: {long_term.get('total_stocks', 0)}")
                print(f"   成功: {long_term.get('success_count', 0)}銘柄")
                print(f"   失敗: {long_term.get('failed_count', 0)}銘柄")
            else:
                print(f"\n⚠️  長期レポート: 生成失敗 ({long_term.get('message', '不明')})")
            
            # 一覧ページ結果
            index = result['index']
            print(f"\n📋 一覧ページ:")
            print(f"   対象銘柄数: {index.get('total_stocks', 0)}")
            print(f"   成功: {index.get('successful_stocks', 0)}銘柄")
            print(f"   失敗: {len(index.get('failed_stocks', []))}銘柄")
            
            print(f"\n📍 生成されたファイル:")
            print(f"   短期レポート: reports/short_term/")
            print(f"   長期レポート: reports/long_term/")
            print(f"   一覧ページ: reports/index.html")
            
        else:
            print(f"\n❌ 全レポート生成失敗: {result['message']}")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"メイン処理中にエラー: {e}")
        print(f"\n❌ エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
