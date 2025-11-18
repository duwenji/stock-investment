import pandas as pd
import sys
import os
from sqlalchemy import create_engine, Column, String, Date, Text, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SQLAlchemy モデル定義
Base = declarative_base()

class Stock(Base):
    """stocksテーブルのORMモデル"""
    __tablename__ = 'stocks'
    
    stock_code = Column(String(10), primary_key=True)
    stock_name = Column(String(100), nullable=False)
    industry = Column(String(50))
    market = Column(String(20))
    description = Column(Text)
    listed_date = Column(Date)
    website = Column(String(200))
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    data_date = Column(Date)
    industry_code_33 = Column(String(10))
    industry_code_17 = Column(String(10))
    scale_code = Column(String(10))
    scale_category = Column(String(50))

def get_database_engine():
    """データベース接続エンジンを取得"""
    # 環境変数から接続情報を取得
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # postgres-mcpから取得した正しい接続情報を使用
        database_url = "postgresql://postgres:postgres@localhost:5432/mcp-postgres-db"
    
    logger.info(f"データベース接続URL: {database_url}")
    engine = create_engine(database_url)
    return engine

def import_stocks_data_with_sqlalchemy():
    """
    ExcelファイルからstocksテーブルにデータをインポートするSQLAlchemy版スクリプト
    """
    try:
        # データベース接続設定
        engine = get_database_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Excelファイルの読み込み
        logger.info("Excelファイルを読み込み中...")
        df = pd.read_excel('../data/data_j.xls')
        logger.info(f"読み込んだデータ: {df.shape[0]}行, {df.shape[1]}列")
        
        # データの前処理
        logger.info("データの前処理中...")
        
        # 日付の変換 (YYYYMMDD形式からDATE型へ)
        df['data_date'] = pd.to_datetime(df['日付'], format='%Y%m%d').dt.date
        
        # 必要なカラムのマッピング
        processed_data = []
        for _, row in df.iterrows():
            # データのクレンジング
            stock_code = str(row['コード']).strip()
            stock_name = str(row['銘柄名']).strip()
            market = str(row['市場・商品区分']).strip()
            industry_33 = str(row['33業種区分']).strip() if pd.notna(row['33業種区分']) else None
            industry_code_33 = str(row['33業種コード']).strip() if pd.notna(row['33業種コード']) else None
            industry_code_17 = str(row['17業種コード']).strip() if pd.notna(row['17業種コード']) else None
            industry_17 = str(row['17業種区分']).strip() if pd.notna(row['17業種区分']) else None
            scale_code = str(row['規模コード']).strip() if pd.notna(row['規模コード']) else None
            scale_category = str(row['規模区分']).strip() if pd.notna(row['規模区分']) else None
            
            # 業種情報の優先順位: 33業種区分 > 17業種区分
            industry = industry_33 if industry_33 and industry_33 != '-' else industry_17
            
            # 文字列長制限の適用
            processed_data.append({
                'stock_code': stock_code[:10] if stock_code else None,
                'stock_name': stock_name[:100] if stock_name else None,
                'industry': industry[:50] if industry else None,
                'market': market[:20] if market else None,
                'description': f"{industry_33 or industry_17 or ''} - {scale_category or ''}"[:500],
                'data_date': row['data_date'],
                'industry_code_33': industry_code_33[:10] if industry_code_33 else None,
                'industry_code_17': industry_code_17[:10] if industry_code_17 else None,
                'scale_code': scale_code[:10] if scale_code else None,
                'scale_category': scale_category[:50] if scale_category else None
            })
        
        logger.info(f"処理済みデータ: {len(processed_data)}件")
        
        # 既存データの削除
        logger.info("既存データを削除中...")
        session.query(Stock).delete()
        
        # バッチ処理によるデータ投入
        logger.info("データをデータベースに投入中...")
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(processed_data), batch_size):
            batch = processed_data[i:i + batch_size]
            stock_objects = []
            
            for data in batch:
                stock = Stock(
                    stock_code=data['stock_code'],
                    stock_name=data['stock_name'],
                    industry=data['industry'],
                    market=data['market'],
                    description=data['description'],
                    data_date=data['data_date'],
                    industry_code_33=data['industry_code_33'],
                    industry_code_17=data['industry_code_17'],
                    scale_code=data['scale_code'],
                    scale_category=data['scale_category'],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                stock_objects.append(stock)
            
            # バッチ挿入
            session.bulk_save_objects(stock_objects)
            session.commit()
            
            total_inserted += len(stock_objects)
            logger.info(f"進捗: {total_inserted}/{len(processed_data)} 件投入完了")
        
        # 最終確認
        count = session.query(Stock).count()
        logger.info(f"データ投入完了: 合計 {count} 件のデータが登録されました")
        
        # サンプルデータの表示
        logger.info("\nサンプルデータ (最初の5件):")
        sample_stocks = session.query(Stock).limit(5).all()
        for i, stock in enumerate(sample_stocks):
            logger.info(f"{i+1}. {stock.stock_code} - {stock.stock_name} - {stock.market}")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

def test_data_processing():
    """データ処理のテスト（実際のデータ投入なし）"""
    try:
        logger.info("データ処理のテストを開始...")
        df = pd.read_excel('../data/data_j.xls')
        
        # データの前処理
        df['data_date'] = pd.to_datetime(df['日付'], format='%Y%m%d').dt.date
        
        processed_data = []
        for _, row in df.iterrows():
            stock_code = str(row['コード']).strip()
            stock_name = str(row['銘柄名']).strip()
            market = str(row['市場・商品区分']).strip()
            
            processed_data.append({
                'stock_code': stock_code,
                'stock_name': stock_name,
                'market': market
            })
        
        logger.info(f"テスト成功: {len(processed_data)}件のデータを処理可能")
        logger.info("サンプルデータ:")
        for i, data in enumerate(processed_data[:3]):
            logger.info(f"  {i+1}. {data['stock_code']} - {data['stock_name']} - {data['market']}")
        
        return True
        
    except Exception as e:
        logger.error(f"テスト失敗: {str(e)}")
        return False

if __name__ == "__main__":
    print("株式データインポートスクリプト (SQLAlchemy版)")
    print("=" * 50)
    
    # テストモードの確認
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print("テストモードで実行します...")
        success = test_data_processing()
    else:
        print("本番モードで実行します...")
        success = import_stocks_data_with_sqlalchemy()
    
    if success:
        print("\n✅ 処理が正常に完了しました")
    else:
        print("\n❌ 処理に失敗しました")
        sys.exit(1)
