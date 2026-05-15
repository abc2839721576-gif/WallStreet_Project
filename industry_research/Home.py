import streamlit as st
import akshare as ak
import pandas as pd

st.set_page_config(
    page_title="WallStreet Intelligence Hub | 华尔街智库平台",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', 'Microsoft YaHei', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .hero-title {
        font-size: 3rem; font-weight: 800; line-height: 1.2;
        background: linear-gradient(135deg, #3B82F6, #06B6D4, #8B5CF6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .module-card {
        background: rgba(15,23,42,0.8);
        border: 1px solid rgba(59,130,246,0.2);
        border-radius: 16px; padding: 24px;
        transition: all 0.3s ease;
    }
    .tag {
        display: inline-block; padding: 2px 10px; border-radius: 999px;
        font-size: 0.75rem; font-weight: 600; margin: 2px;
    }
    hr { border:0; height:1px; background: linear-gradient(to right, rgba(0,0,0,0), rgba(59,130,246,0.5), rgba(0,0,0,0)); margin: 1.5rem 0; }
    </style>
""", unsafe_allow_html=True)

# ── Hero Section ──────────────────────────────────────────────
col_hero, col_badge = st.columns([3, 1])
with col_hero:
    st.markdown('<div class="hero-title">WallStreet Intelligence Hub</div>', unsafe_allow_html=True)
    st.markdown("#### 华尔街智库平台 · 行业研究 × 基金量化 × NLP 情报")
    st.markdown(
        "🎓 **张君瑞** · 青岛大学 材料科学与工程 + 金融学 · "
        "数据分析师方向 · 韩国交换生"
    )
with col_badge:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("📡 实时数据\n\n🧠 NLP 驱动\n\n🌐 中英双语")

st.markdown("---")

# ── 实时宏观指标 ─────────────────────────────────────────────
st.subheader("🌍 实时宏观脉冲")
try:
    macro_cols = st.columns(5)
    indicators = [
        ("上证指数", "000001", "SH"),
        ("深证成指", "399001", "SZ"),
        ("创业板指", "399006", "SZ"),
        ("沪深300", "000300", "SH"),
        ("科创50",   "000688", "SH"),
    ]
    df_spot = ak.stock_zh_index_spot_sina()
    name_map = {"上证指数": "000001", "深证成指": "399001",
                "创业板指": "399006", "沪深300": "000300", "科创50": "000688"}
    for i, (name, code, ex) in enumerate(indicators):
        row = df_spot[df_spot["名称"] == name]
        if not row.empty:
            r = row.iloc[0]
            macro_cols[i].metric(name, f"{float(r['最新价']):.2f}", f"{float(r['涨跌幅']):.2f}%", delta_color="inverse")
except Exception:
    st.warning("暂无法获取实时行情，请检查网络。")

st.markdown("---")

# ── 模块导航卡片 ─────────────────────────────────────────────
st.subheader("📚 研究模块导航")
st.caption("点击左侧侧边栏进入各模块，或参考下方模块介绍")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown("#### 📈 基金量化看板")
    st.markdown("- 多源数据自动降级抓取\n- K-Means 聚类风格识别\n- Random Forest 因子归因\n- 相关性对冲推荐引擎")
    st.markdown("`AkShare` `sklearn` `Plotly`")
    st.info("📂 启动：`dashboard/fund_dashboard.py`")

with m2:
    st.markdown("#### 🏭 行业宏观数据")
    st.markdown("- 半导体 / 新能源 / 新材料\n- 中韩产业链横向对比\n- PMI / CPI / 产值趋势\n- AkShare 宏观数据接入")
    st.markdown("`AkShare` `Pandas` `Plotly`")
    st.success("✅ 本平台 → 侧边栏「行业研究」")

with m3:
    st.markdown("#### 📰 政策雷达站")
    st.markdown("- 国家发改委 / 证监会公告\n- TF-IDF 关键词自动提取\n- 行业标签自动打标\n- 政策时间轴可视化")
    st.markdown("`jieba` `TF-IDF` `BeautifulSoup`")
    st.success("✅ 本平台 → 侧边栏「政策雷达」")

with m4:
    st.markdown("#### 🧠 研报智能摘要")
    st.markdown("- 中英文研报 NLP 分析\n- SnowNLP / TextBlob 情感\n- 东方财富研报聚合\n- 词云图 + 关键词排行")
    st.markdown("`SnowNLP` `TextBlob` `wordcloud`")
    st.success("✅ 本平台 → 侧边栏「研报智库」")

st.markdown("---")

# ── 关于开发者 ───────────────────────────────────────────────
st.subheader("👨‍💻 关于开发者")
dev1, dev2, dev3 = st.columns(3)
with dev1:
    st.markdown("""
    **张君瑞 (Zhang Junrui)**  
    🎓 青岛大学 · 材料科学与工程（本科）+ 金融学（辅修）  
    🌏 韩国交换生 · 国际视野  
    💼 求职意向：**数据分析师 / 量化研究**
    """)
with dev2:
    st.markdown("""
    **核心能力栈**  
    `Python` `SQL (MySQL)` `Pandas` `NumPy`  
    `Scikit-learn` `Streamlit` `Plotly`  
    `NLP (jieba / SnowNLP)` `LLM / AI Agent`
    """)
with dev3:
    st.markdown("""
    **证书与资质**  
    📜 CESTEC 大数据分析工程师（中级）  
    📜 基金从业资格证  
    📜 全国计算机等级（二级）  
    📧 2839721576@qq.com
    """)

st.caption("Powered by WallStreet Intelligence Hub · Steward Agent 统筹开发")
