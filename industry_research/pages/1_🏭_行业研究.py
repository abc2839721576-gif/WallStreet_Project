"""
行业宏观数据页面
聚焦：半导体 / 新能源材料 / 金融科技
数据来源：AkShare 宏观数据接口
"""
import streamlit as st
import akshare as ak
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

st.set_page_config(page_title="行业研究 | WallStreet Hub", page_icon="🏭", layout="wide")

PLOTLY_TEMPLATE = "plotly_dark"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', 'Microsoft YaHei', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🏭 行业宏观研究中心")
st.caption("Industry Macro Research Center | 聚焦：半导体 · 新能源材料 · 金融科技")
st.markdown("---")

# ── 数据加载函数 ──────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_pmi():
    try:
        df = ak.macro_china_pmi_yearly()
        df.columns = [str(c) for c in df.columns]
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def load_cpi():
    try:
        df = ak.macro_china_cpi_yearly()
        df.columns = [str(c) for c in df.columns]
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def load_gdp():
    try:
        df = ak.macro_china_gdp_yearly()
        df.columns = [str(c) for c in df.columns]
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def load_sector_index(sector_code):
    try:
        df = ak.stock_board_industry_hist_em(
            symbol=sector_code, period="日k", start_date="20220101",
            end_date=pd.Timestamp.now().strftime("%Y%m%d"), adjust=""
        )
        df['日期'] = pd.to_datetime(df['日期'])
        return df
    except Exception as e:
        return None

# ── 板块选择器 ────────────────────────────────────────────────
st.subheader("🏗️ 行业板块选择")
SECTORS = {
    "半导体 (Semiconductors)":     "半导体",
    "锂电池 (Li-Battery)":          "锂电池",
    "光伏设备 (Solar/PV)":          "光伏设备",
    "新材料 (New Materials)":       "新材料",
    "金融科技 (FinTech)":           "互联网金融",
    "银行 (Banking)":               "银行",
}

col_sel1, col_sel2 = st.columns([2, 1])
with col_sel1:
    selected_sector_label = st.selectbox(
        "选择目标行业板块 (基于您的背景：材料科学 + 金融学)：",
        list(SECTORS.keys())
    )
with col_sel2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"🔍 当前：**{selected_sector_label}**")

sector_name = SECTORS[selected_sector_label]

# ── 行业板块走势 ──────────────────────────────────────────────
st.markdown("---")
st.subheader(f"📈 {selected_sector_label} 板块指数走势")

with st.spinner(f"正在加载 {sector_name} 板块数据..."):
    df_sector = load_sector_index(sector_name)

if df_sector is not None and not df_sector.empty:
    fig_sec = go.Figure()
    fig_sec.add_trace(go.Candlestick(
        x=df_sector['日期'],
        open=df_sector['开盘'], high=df_sector['最高'],
        low=df_sector['最低'], close=df_sector['收盘'],
        name=sector_name
    ))
    # 20日均线
    df_sector['MA20'] = df_sector['收盘'].rolling(20).mean()
    fig_sec.add_trace(go.Scatter(
        x=df_sector['日期'], y=df_sector['MA20'],
        mode='lines', name='MA20', line=dict(color='#06B6D4', width=1.5, dash='dot')
    ))
    fig_sec.update_layout(
        title=f"{sector_name} 板块 K 线图（日K）",
        template=PLOTLY_TEMPLATE, height=480,
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig_sec, use_container_width=True)
    
    # 成交额趋势
    if '成交额' in df_sector.columns:
        fig_vol = px.bar(df_sector.tail(60), x='日期', y='成交额',
                         title=f"{sector_name} 近 60 日成交额趋势",
                         color='涨跌幅' if '涨跌幅' in df_sector.columns else None,
                         color_continuous_scale='RdYlGn', template=PLOTLY_TEMPLATE)
        st.plotly_chart(fig_vol, use_container_width=True)
else:
    st.warning(f"暂无法获取 {sector_name} 板块数据，请检查网络或稍后重试。")

# ── 宏观三大指标 ──────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 宏观经济三大脉搏 (PMI · CPI · GDP)")
st.markdown("*Macro Economic Indicators: Manufacturing PMI · Consumer Price Index · GDP Growth*")

tab_pmi, tab_cpi, tab_gdp = st.tabs(["🏗️ PMI 制造业", "🛒 CPI 通胀", "💹 GDP 增速"])

with tab_pmi:
    with st.spinner("加载 PMI 数据..."):
        df_pmi = load_pmi()
    if df_pmi is not None and not df_pmi.empty:
        st.dataframe(df_pmi.head(20), use_container_width=True)
        try:
            # 尝试绘图
            df_pmi_plot = df_pmi.copy()
            numeric_cols = df_pmi_plot.select_dtypes(include='number').columns.tolist()
            date_col = [c for c in df_pmi_plot.columns if '时间' in c or '年' in c or '日期' in c]
            if date_col and numeric_cols:
                fig_pmi = px.line(df_pmi_plot, x=date_col[0], y=numeric_cols[0],
                                  title="中国制造业 PMI 趋势", template=PLOTLY_TEMPLATE)
                fig_pmi.add_hline(y=50, line_dash="dot", line_color="#EF4444",
                                  annotation_text="荣枯线 50")
                st.plotly_chart(fig_pmi, use_container_width=True)
        except Exception:
            pass
    else:
        st.info("PMI 数据加载失败，请稍后重试。")

with tab_cpi:
    with st.spinner("加载 CPI 数据..."):
        df_cpi = load_cpi()
    if df_cpi is not None and not df_cpi.empty:
        st.dataframe(df_cpi.head(20), use_container_width=True)
    else:
        st.info("CPI 数据加载失败，请稍后重试。")

with tab_gdp:
    with st.spinner("加载 GDP 数据..."):
        df_gdp = load_gdp()
    if df_gdp is not None and not df_gdp.empty:
        st.dataframe(df_gdp.head(20), use_container_width=True)
        try:
            numeric_cols = df_gdp.select_dtypes(include='number').columns.tolist()
            date_col = [c for c in df_gdp.columns if '时间' in c or '年' in c or '季' in c]
            if date_col and numeric_cols:
                fig_gdp = px.bar(df_gdp.head(30), x=date_col[0], y=numeric_cols[0],
                                 title="中国 GDP 历年增速", template=PLOTLY_TEMPLATE,
                                 color=numeric_cols[0], color_continuous_scale='Blues')
                st.plotly_chart(fig_gdp, use_container_width=True)
        except Exception:
            pass
    else:
        st.info("GDP 数据加载失败，请稍后重试。")

# ── 中韩产业链对比 ────────────────────────────────────────────
st.markdown("---")
st.subheader("🌏 中韩产业链横向对比视角")
st.markdown("""
*基于您的韩国交换生背景，以下是中韩在核心行业的产业链对比*

| 行业 | 中国优势 | 韩国优势 | 竞合关系 |
|------|---------|---------|---------|
| **半导体** | 市场需求（全球最大消费国）、封测、部分设计 | 存储芯片（三星/SK 海力士全球第一）、OLED 显示 | 竞争+依赖：中国大量进口韩国存储 |
| **新能源电池** | 锂电池产量全球 70%+（CATL/BYD）、正负极材料 | 三星SDI / LG 新能源 - 圆柱电池全球领先 | 激烈竞争：同时在欧美供应链抢份额 |
| **新材料** | 稀土（全球 60% 储量）、碳纤维产能扩张 | 特殊钢材、碳纤维高端应用、显示材料 | 互补：中国供应原料，韩国深加工 |
| **金融科技** | 移动支付全球领先（支付宝/微信）、数字人民币 | 互联网银行（Kakao Bank）、数据经济 | 独立发展，韩国借鉴中国经验 |
""")
