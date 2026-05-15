import streamlit as st
import akshare as ak
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared_style import inject_bloomberg_css

st.set_page_config(
    page_title="WallStreet Hub | AI-Powered Intelligence",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 注入 Bloomberg Lite CSS（背景由 config.toml 控制）──
inject_bloomberg_css()

# ── 页面专用 CSS（Hero / KPI / 表格等自定义组件） ──
st.markdown("""
<style>
.metric-card, .info-card {
    background-color: #131A2E;
    backdrop-filter: blur(12px);
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.06);
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    transition: all 0.25s ease;
    margin-bottom: 16px;
}
.metric-card:hover, .info-card:hover {
    transform: translateY(-3px);
    background-color: #1D2742;
    border: 1px solid rgba(0,194,255,0.3);
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
}
.hero-title {
    font-size: 3.2rem; font-weight: 800; color: #E2E8F0; margin-bottom: 0;
}
.hero-subtitle {
    font-size: 1.6rem; font-weight: 600; color: #00C2FF; margin-top: 5px;
}
.hero-desc {
    font-size: 1.05rem; color: #94A3B8; margin-top: 10px; letter-spacing: 0.5px;
}
.kpi-value {
    font-size: 2rem; font-weight: 700; margin: 5px 0;
}
.kpi-value.green { color: #2ECC71; text-shadow: 0 0 10px rgba(46,204,113,0.3); }
.kpi-value.red   { color: #FF5A5F; text-shadow: 0 0 10px rgba(255,90,95,0.3); }
.kpi-value.blue  { color: #00C2FF; text-shadow: 0 0 10px rgba(0,194,255,0.3); }
.kpi-value.yellow{ color: #FFD166; text-shadow: 0 0 10px rgba(255,209,102,0.3); }
.brand-footer {
    text-align: center; color: #64748B; font-size: 0.85rem;
    margin-top: 50px; padding-top: 20px;
    border-top: 1px solid rgba(255,255,255,0.05);
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# Hero Section
# ══════════════════════════════════════════
col_hero, col_stats = st.columns([1.5, 1])

with col_hero:
    st.markdown('<div class="hero-title">WallStreet Hub</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">AI-Driven Industry Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-desc">Real-time Macro Research · Sector Rotation Analytics · Quantitative Insight Engine</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

with col_stats:
    st.markdown("""
    <div class="info-card" style="padding: 18px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span style="color: #94A3B8;">今日监测行业</span>
            <span style="color: #00C2FF; font-weight: bold;">12</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span style="color: #94A3B8;">数据源</span>
            <span style="color: #00C2FF; font-weight: bold;">38+</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span style="color: #94A3B8;">更新频率</span>
            <span style="color: #2ECC71; font-weight: bold;">实时 (Real-time)</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #94A3B8;">AI评分模型</span>
            <span style="color: #FFD166; font-weight: bold;">● Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# KPI 四宫格
# ══════════════════════════════════════════
k1, k2, k3, k4 = st.columns(4)
kpis = [
    (k1, "SECTOR MOMENTUM", "+8.4%", "green", "Strong Uptrend"),
    (k2, "RISK INDEX", "32", "yellow", "Moderate (VIX-based)"),
    (k3, "MACRO SCORE", "78/100", "blue", "Expansion Phase"),
    (k4, "ALPHA SIGNAL", "BUY", "green", "Quant Model Activated")
]

for col, title, val, color, desc in kpis:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.8rem; color: #94A3B8; font-weight: 600; letter-spacing: 1px;">{title}</div>
            <div class="kpi-value {color}">{val}</div>
            <div style="font-size: 0.78rem; color: #64748B;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════
# 实时大盘 (Market Pulse)
# ══════════════════════════════════════════
st.markdown("#### ⚡ 实时大盘监测 (Market Pulse)")
try:
    df_spot = ak.stock_zh_index_spot_sina()
    watch_list = ["上证指数", "深证成指", "创业板指", "沪深300", "科创50"]
    filtered_df = df_spot[df_spot["名称"].isin(watch_list)]

    if not filtered_df.empty:
        html_table = '<table style="width:100%; text-align:left; border-collapse: collapse;">'
        html_table += '<tr style="border-bottom: 1px solid rgba(255,255,255,0.1); color: #94A3B8; font-size: 0.85rem;">'
        html_table += '<th style="padding: 10px;">指数名称</th><th style="padding: 10px;">最新价</th><th style="padding: 10px;">涨跌额</th><th style="padding: 10px;">涨跌幅(%)</th></tr>'
        for _, row in filtered_df.iterrows():
            pct = float(row.get('涨跌幅', 0))
            color = "#2ECC71" if pct >= 0 else "#FF5A5F"
            sign = "+" if pct >= 0 else ""
            html_table += f'<tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">'
            html_table += f'<td style="padding: 11px; font-weight: 500;">{row["名称"]}</td>'
            html_table += f'<td style="padding: 11px; color: {color};">{row["最新价"]}</td>'
            html_table += f'<td style="padding: 11px; color: {color};">{sign}{row["涨跌额"]}</td>'
            html_table += f'<td style="padding: 11px; color: {color};">{sign}{pct}%</td>'
            html_table += '</tr>'
        html_table += '</table>'
        st.markdown(f'<div class="info-card">{html_table}</div>', unsafe_allow_html=True)
    else:
        st.info("未能匹配到指定指数数据。")

except Exception:
    st.warning("暂无法获取实时行情，请检查网络。")

st.markdown("---")

# ══════════════════════════════════════════
# 模块导航卡片
# ══════════════════════════════════════════
st.markdown("#### 📚 研究模块")
m1, m2, m3 = st.columns(3)

with m1:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 8px;">📈 基金量化看板</div>
        <div style="color: #94A3B8; font-size: 0.9rem; line-height: 1.8;">
        多源数据降级抓取<br>K-Means 聚类风格识别<br>Random Forest 因子归因<br>相关性对冲推荐引擎
        </div>
        <div style="margin-top: 10px; color: #00C2FF; font-size: 0.8rem;">AkShare · sklearn · Plotly</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 8px;">🏭 行业宏观数据</div>
        <div style="color: #94A3B8; font-size: 0.9rem; line-height: 1.8;">
        半导体 / 新能源 / 新材料<br>中韩产业链横向对比<br>PMI / CPI / 产值趋势<br>AkShare 宏观数据接入
        </div>
        <div style="margin-top: 10px; color: #00C2FF; font-size: 0.8rem;">AkShare · Pandas · Plotly</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 8px;">📡 政策雷达 & 研报</div>
        <div style="color: #94A3B8; font-size: 0.9rem; line-height: 1.8;">
        TF-IDF 关键词自动提取<br>SnowNLP / TextBlob 情感分析<br>东方财富研报聚合<br>词云图 + 关键词排行
        </div>
        <div style="margin-top: 10px; color: #00C2FF; font-size: 0.8rem;">jieba · SnowNLP · TextBlob</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════
# 关于开发者
# ══════════════════════════════════════════
st.markdown("#### 👨‍💻 关于开发者")
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

# ── Footer ──
st.markdown("""
<div class="brand-footer">
    WallStreet Hub © 2026<br>
    Built by Junrui Zhang<br>
    FinTech Research System
</div>
""", unsafe_allow_html=True)
