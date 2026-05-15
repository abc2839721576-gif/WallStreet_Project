import akshare as ak
import pandas as pd
import os
import sys

# 解决 Windows 控制台默认 GBK 编码导致无法打印 Emoji 的报错
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class WallStreetAgent:
    def __init__(self, data_dir="./wallstreet_data"):
        """
        初始化华尔街 Agent 的数据工作区
        """
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"📁 已创建华尔街专属数据工作区: {self.data_dir}")

    def fetch_all_funds_list(self):
        """
        获取全市场公募基金列表并保存
        """
        print("⏳ 正在请求全市场公募基金列表，这可能需要几秒钟...")
        try:
            # 获取天天基金网的开放式基金数据
            funds_df = ak.fund_em_fund_name()
            
            # 保存到本地 CSV
            file_path = os.path.join(self.data_dir, "all_mutual_funds.csv")
            funds_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            print(f"✅ 成功获取全市场 {len(funds_df)} 只基金的基本信息！")
            print(f"💾 数据已保存至: {file_path}")
            return funds_df
        except Exception as e:
            print(f"❌ 获取基金列表失败: {e}")
            return None

    def fetch_fund_history(self, fund_code: str):
        """
        获取指定基金的历史净值数据
        """
        print(f"⏳ 正在获取基金 {fund_code} 的历史净值走势...")
        try:
            # akshare 的 fund_open_fund_info_em 接口获取开放式基金历史净值
            fund_data = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
            
            if fund_data.empty:
                print(f"⚠️ 未能获取到基金 {fund_code} 的数据，请检查代码。")
                return None
                
            # 数据清洗：转换日期格式并按时间排序
            fund_data['净值日期'] = pd.to_datetime(fund_data['净值日期'])
            fund_data = fund_data.sort_values('净值日期')
            
            # 保存为 CSV
            file_path = os.path.join(self.data_dir, f"fund_{fund_code}_history.csv")
            fund_data.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            print(f"✅ 成功！基金 {fund_code} 共获取到 {len(fund_data)} 条历史交易日数据。")
            print(f"💾 数据已保存至: {file_path}")
            return fund_data
            
        except Exception as e:
            print(f"❌ 获取基金 {fund_code} 历史数据失败: {e}")
            return None

if __name__ == "__main__":
    print("🤖 华尔街 Agent (Wall Street) 正在启动一阶段数据工程...")
    agent = WallStreetAgent()
    
    # 任务1: 获取全市场基金列表 (如需全量更新，可以取消下面这行的注释)
    # agent.fetch_all_funds_list()  
    
    # 任务2: 测试获取特定明星基金（如: 易方达蓝筹精选混合 005827）
    test_fund = "005827"
    agent.fetch_fund_history(test_fund)
    
    print("\n🎉 阶段一：数据获取自动化初步跑通！")
