import pandas as pd
from sqlalchemy import create_engine
import os
import sys

# 解决 Windows 控制台输出问题
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# MySQL 连接配置 (从你之前的 db_query.py 中读取)
DB_USER = 'root'
DB_PASSWORD = '123456'
DB_HOST = 'localhost'
DB_NAME = 'finance_ai'

def import_excel_to_mysql(file_paths):
    """
    将指定的 Excel 文件读取并写入 MySQL 数据库
    """
    # 创建 SQLAlchemy 引擎
    try:
        engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4")
        print(f"✅ 成功连接到 MySQL 数据库: {DB_NAME}")
    except Exception as e:
        print(f"❌ 数据库连接失败，请检查 MySQL 服务是否开启: {e}")
        return

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"⚠️ 找不到文件: {file_path}")
            continue
            
        print(f"⏳ 正在读取 Excel 文件: {os.path.basename(file_path)} (这可能需要一些时间...)")
        try:
            # 读取 Excel
            df = pd.read_excel(file_path)
            
            # 清洗：去除列名中的前后空格
            df.columns = df.columns.str.strip()
            
            # 表名处理 (提取年份等作为表名)
            table_name = "fund_holdings_" + os.path.basename(file_path).replace('基金重仓数据.xlsx', '')
            
            print(f"⏳ 正在将数据写入数据表 '{table_name}' 中...")
            # 写入 MySQL
            # if_exists='replace' 表示如果表存在则覆盖，'append' 表示追加
            df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
            
            print(f"🎉 成功！文件 {os.path.basename(file_path)} 的 {len(df)} 条数据已存入数据库表: {table_name}")
            
        except Exception as e:
            print(f"❌ 处理文件 {file_path} 时发生错误: {e}")

if __name__ == "__main__":
    files_to_import = [
        r"C:\Users\86155\Desktop\青岛大学_张君瑞\1.数据源\2018基金重仓数据.xlsx",
        r"C:\Users\86155\Desktop\青岛大学_张君瑞\1.数据源\2019基金重仓数据.xlsx"
    ]
    
    print("🤖 华尔街 Agent 正在启动数据入库工作...")
    import_excel_to_mysql(files_to_import)
