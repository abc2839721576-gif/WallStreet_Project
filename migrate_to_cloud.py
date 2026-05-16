import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

def migrate_database():
    print("🚀 开始数据搬运任务...")

    # 1. 配置本地数据库地址
    local_url = "mysql+pymysql://root:123456@localhost/finance_ai?charset=utf8mb4"
    local_engine = create_engine(local_url)

    # 2. 从 secrets.toml 获取云端数据库地址
    try:
        cloud_url = st.secrets["DB_URL"]
        print("✅ 成功读取到云端数据库密钥")
    except Exception as e:
        print("❌ 错误：无法读取 .streamlit/secrets.toml，请确认文件存在且拼写正确。")
        return

    # 3. 确保云端已经创建了 finance_ai 这个数据库
    # 因为刚申请的 TiDB 默认只有 test 数据库，我们要先把连接里的 finance_ai 换成 test 来连
    base_cloud_url = cloud_url.replace('/finance_ai', '/test')
    init_engine = create_engine(base_cloud_url)
    
    try:
        with init_engine.connect() as conn:
            conn.execute(text("CREATE DATABASE IF NOT EXISTS finance_ai;"))
            print("✅ 成功在云端创建 finance_ai 数据库")
    except Exception as e:
        print(f"⚠️ 创建云端数据库时出现提示（可能是已经存在）: {e}")

    # 4. 正式连接到云端的 finance_ai
    cloud_engine = create_engine(cloud_url)

    # 5. 获取本地所有表名
    print("\n🔍 正在扫描本地数据表...")
    try:
        with local_engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES;"))
            tables = [row[0] for row in result]
    except Exception as e:
        print(f"❌ 无法连接本地 MySQL，请确保本地 MySQL 已启动且密码是 123456。报错: {e}")
        return

    if not tables:
        print("⚠️ 本地数据库里没有任何表，无需迁移。")
        return

    print(f"发现 {len(tables)} 张表：{tables}")

    # 6. 开始逐一迁移表
    for table in tables:
        print(f"\n⏳ 正在搬运表: {table} ...")
        try:
            # 从本地读取数据到内存 (DataFrame)
            df = pd.read_sql_table(table, local_engine)
            print(f"   读取到 {len(df)} 行数据，准备上传云端...")
            
            # 将数据写入云端数据库 (如果存在就替换)
            df.to_sql(table, cloud_engine, if_exists='replace', index=False, chunksize=5000)
            print(f"   🎉 表 {table} 搬运成功！")
        except Exception as e:
            print(f"   ❌ 表 {table} 搬运失败，报错: {e}")

    print("\n🎉🎉 恭喜！所有数据搬运完毕！你的云数据库现在已经有数据了！")

if __name__ == "__main__":
    migrate_database()
