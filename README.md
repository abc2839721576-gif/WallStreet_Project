# WallStreet Project | 华尔街智能体

> 张君瑞 | 青岛大学 | 数据分析师方向

## 项目结构

```
WallStreet_Project/
├── dashboard/                  # 基金分析看板 (Streamlit)
│   ├── fund_dashboard.py       # 主程序 (六大功能模块)
│   ├── wallstreet_data_fetcher.py  # AkShare 数据抓取脚本
│   ├── import_excel_to_mysql.py    # Excel → MySQL 导入脚本
│   ├── .streamlit/config.toml  # 主题配置 (Dark FinTech)
│   └── wallstreet_data/        # 本地基金净值缓存
│
├── portfolio/                  # 个人简历网站 (纯前端)
│   ├── index.html              # 页面结构
│   ├── style.css               # Dark FinTech 样式
│   ├── script.js               # 交互动画逻辑
│   └── profile.jpg             # 简历照片
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 数据获取 | AkShare API, MySQL |
| 数据处理 | Pandas, NumPy, Scikit-learn |
| 可视化 | Streamlit, Plotly |
| 前端 | HTML5, CSS3, JavaScript |
| 数据库 | MySQL (finance_ai) |

## 启动方式

```bash
# 启动基金分析看板
cd dashboard
streamlit run fund_dashboard.py

# 启动个人简历网页
cd portfolio
python -m http.server 8080
```

## 联系方式

- 📧 2839721576@qq.com
