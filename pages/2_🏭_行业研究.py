"""
行业宏观数据页面
聚焦：半导体 / 新能源材料 / 金融科技
数据策略：ETF 指数追踪（稳定可靠）+ AkShare 宏观接口 + 本地缓存
"""
import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_style import inject_bloomberg_css

st.set_page_config(page_title="Industry Research | WallStreet Hub", page_icon="🏭", layout="wide")
PLOTLY_TEMPLATE = "plotly_dark"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "industry_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

inject_bloomberg_css()

st.title("🏭 行业宏观研究中心")
st.caption("Industry Macro Research Center | 聚焦：半导体 · 新能源材料 · 金融科技")
st.markdown("---")

# ══════════════════════════════════════════
# 数据策略说明：
# 东方财富行业板块 API (stock_board_industry_hist_em) 在韩国被服务器拒绝，
# 因此改用 ETF 行情接口（fund_etf_hist_em）追踪行业走势。
# ETF 数据稳定可靠，且更贴近真实可交易标的。
# 同时加入本地 JSON 缓存，减少重复请求。
# ══════════════════════════════════════════

# ── 行业 ETF 映射表 ────────────────────────────────────────────
SECTOR_ETFS = {
    "半导体": {"etf": "512480", "name": "国联安中证半导体ETF", "desc": "追踪中证全指半导体指数"},
    "锂电池": {"etf": "159840", "name": "鹏华国证新能源车ETF", "desc": "追踪新能源车产业链"},
    "光伏设备": {"etf": "515790", "name": "华泰柏瑞光伏ETF", "desc": "追踪中证光伏产业指数"},
    "新材料":  {"etf": "159761", "name": "天弘中证新材料ETF", "desc": "追踪中证新材料主题指数"},
    "金融科技": {"etf": "159851", "name": "华夏中证金融科技ETF", "desc": "追踪金融科技主题指数"},
    "银行":    {"etf": "512800", "name": "华宝中证银行ETF", "desc": "追踪中证银行指数"},
}

# ── 通用数据加载（带本地 JSON 缓存）──────────────────────────────

def _load_with_cache(cache_key, fetch_func, ttl_hours=6):
    """先查本地缓存，过期了才请求网络"""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    # 检查缓存是否存在且未过期
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            cached_time = pd.to_datetime(cached.get('_cached_at', '2000-01-01'))
            if (pd.Timestamp.now() - cached_time).total_seconds() < ttl_hours * 3600:
                df = pd.DataFrame(cached['data'])
                return df, "cache"
        except Exception:
            pass
    
    # 缓存不存在或已过期，从网络获取
    try:
        df = fetch_func()
        if df is not None and not df.empty:
            # 保存到缓存
            cache_data = {
                '_cached_at': pd.Timestamp.now().isoformat(),
                'data': df.to_dict(orient='records')
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, default=str)
            return df, "live"
    except Exception as e:
        pass
    
    # 网络也失败了，尝试读取过期缓存（有总比没有好）
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            df = pd.DataFrame(cached['data'])
            return df, "stale_cache"
        except Exception:
            pass
    
    return None, "failed"


# ── 示例数据生成（海外部署兜底）──────────────────────────────────
def _generate_demo_etf(etf_code):
    """生成模拟 ETF K 线数据用于海外展示"""
    np.random.seed(hash(etf_code) % 2**31)
    dates = pd.date_range(start='2023-01-01', end=pd.Timestamp.now(), freq='B')
    n = len(dates)
    base_price = {"512480": 1.2, "159840": 2.5, "515790": 0.8, "159761": 1.0, "159851": 0.9, "512800": 1.1}.get(etf_code, 1.0)
    
    prices = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0.0002, 0.018)
        prices.append(prices[-1] * (1 + change))
    
    data = []
    for i, date in enumerate(dates):
        close = prices[i]
        high = close * (1 + abs(np.random.normal(0, 0.01)))
        low = close * (1 - abs(np.random.normal(0, 0.01)))
        open_p = low + (high - low) * np.random.random()
        vol = np.random.randint(50000000, 500000000)
        pct = ((close / prices[i-1]) - 1) * 100 if i > 0 else 0
        data.append({"日期": date, "开盘": round(open_p, 4), "收盘": round(close, 4),
                     "最高": round(high, 4), "最低": round(low, 4),
                     "成交额": vol, "涨跌幅": round(pct, 2)})
    return pd.DataFrame(data)

def _generate_demo_macro(indicator):
    """生成模拟宏观数据"""
    if indicator == 'pmi':
        dates = pd.date_range(start='2020-01', periods=60, freq='MS')
        values = [50 + np.random.normal(0.5, 1.2) for _ in range(60)]
        return pd.DataFrame({"日期": dates, "制造业PMI": [round(v, 1) for v in values]})
    elif indicator == 'cpi':
        dates = pd.date_range(start='2020-01', periods=60, freq='MS')
        values = [2.0 + np.random.normal(0, 0.8) for _ in range(60)]
        return pd.DataFrame({"日期": dates, "CPI同比增长": [round(v, 1) for v in values]})
    elif indicator == 'gdp':
        years = [f"{y}年" for y in range(2010, 2026)]
        values = [10.6, 9.5, 7.9, 7.8, 7.3, 7.0, 6.8, 6.9, 6.7, 6.0, 2.2, 8.4, 3.0, 5.2, 5.0, 4.8]
        return pd.DataFrame({"年份": years, "GDP增速%": values})
    return None


def load_etf_data(etf_code):
    """加载 ETF 历史行情（用 fund_etf_hist_em，海外自动降级为模拟数据）"""
    def fetch():
        df = ak.fund_etf_hist_em(
            symbol=etf_code, period="daily",
            start_date="20220101",
            end_date=pd.Timestamp.now().strftime("%Y%m%d"),
            adjust="qfq"
        )
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            return df
        return None
    
    df, source = _load_with_cache(f"etf_{etf_code}", fetch, ttl_hours=4)
    if source == "failed":
        return _generate_demo_etf(etf_code), "demo"
    return df, source


def load_macro(indicator):
    """加载宏观指标（PMI/CPI/GDP），海外自动降级"""
    api_map = {
        'pmi': ak.macro_china_pmi_yearly,
        'cpi': ak.macro_china_cpi_yearly,
        'gdp': ak.macro_china_gdp_yearly,
    }
    def fetch():
        df = api_map[indicator]()
        df.columns = [str(c) for c in df.columns]
        return df
    
    df, source = _load_with_cache(f"macro_{indicator}", fetch, ttl_hours=12)
    if source == "failed":
        return _generate_demo_macro(indicator), "demo"
    return df, source


# ══════════════════════════════════════════
# 行业板块选择 (Tabs)
# ══════════════════════════════════════════
st.subheader("🏗️ 行业板块选择 (Sector Rotation)")

sector_keys = list(SECTOR_ETFS.keys())
tabs = st.tabs(sector_keys)

for i, tab in enumerate(tabs):
    with tab:
        sector = sector_keys[i]
        etf_info = SECTOR_ETFS[sector]
        
        st.markdown(f"**{etf_info['name']}** (`{etf_info['etf']}`) — {etf_info['desc']}")
        
        df_etf, source = load_etf_data(etf_info['etf'])
        
        if source == "demo":
            st.info("🌐 当前显示模拟数据（海外服务器无法连接 AkShare）。国内运行时将自动加载真实行情。")
        elif source == "stale_cache":
            st.info("📦 使用本地缓存数据（API 暂时不可用，数据可能不是最新）")
        elif source == "cache":
            st.caption("⚡ 数据来自本地缓存（快速加载）")
        
        if df_etf is not None and not df_etf.empty:
            # ── K 线图 ──
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df_etf['日期'],
                open=df_etf['开盘'], high=df_etf['最高'],
                low=df_etf['最低'], close=df_etf['收盘'],
                name=sector,
                increasing_line_color='#2ECC71', decreasing_line_color='#FF5A5F'
            ))
            # MA20 均线
            df_etf['MA20'] = df_etf['收盘'].rolling(20).mean()
            df_etf['MA60'] = df_etf['收盘'].rolling(60).mean()
            fig.add_trace(go.Scatter(
                x=df_etf['日期'], y=df_etf['MA20'],
                mode='lines', name='MA20',
                line=dict(color='#00C2FF', width=1.5)
            ))
            fig.add_trace(go.Scatter(
                x=df_etf['日期'], y=df_etf['MA60'],
                mode='lines', name='MA60',
                line=dict(color='#FFD166', width=1.5, dash='dot')
            ))
            fig.update_layout(
                title=f"{sector} 板块 ETF K 线图 ({etf_info['name']})",
                template=PLOTLY_TEMPLATE, height=480,
                xaxis_rangeslider_visible=False,
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # ── 成交额 ──
            if '成交额' in df_etf.columns:
                recent = df_etf.tail(60).copy()
                if '涨跌幅' in recent.columns:
                    recent['涨跌幅'] = pd.to_numeric(recent['涨跌幅'], errors='coerce')
                fig_vol = px.bar(
                    recent, x='日期', y='成交额',
                    title=f"{sector} 近 60 日成交额趋势",
                    color='涨跌幅' if '涨跌幅' in recent.columns else None,
                    color_continuous_scale='RdYlGn', template=PLOTLY_TEMPLATE
                )
                fig_vol.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_vol, use_container_width=True)
            
            # ── 技术指标速览 ──
            latest = df_etf.iloc[-1]
            prev = df_etf.iloc[-2] if len(df_etf) > 1 else latest
            k1, k2, k3, k4 = st.columns(4)
            close_val = float(latest['收盘'])
            change_pct = (close_val / float(prev['收盘']) - 1) * 100 if float(prev['收盘']) > 0 else 0
            ma20_val = float(df_etf['MA20'].iloc[-1]) if pd.notna(df_etf['MA20'].iloc[-1]) else close_val
            ma20_bias = (close_val / ma20_val - 1) * 100
            vol_20 = df_etf['收盘'].pct_change().tail(20).std() * np.sqrt(252) * 100
            
            k1.metric("最新收盘", f"¥{close_val:.3f}", f"{change_pct:+.2f}%")
            k2.metric("MA20偏离", f"{ma20_bias:+.2f}%",
                       "多头" if ma20_bias > 0 else "空头",
                       delta_color="normal" if ma20_bias > 0 else "inverse")
            k3.metric("20日年化波动率", f"{vol_20:.1f}%")
            k4.metric("60日趋势",
                       "↑ 上行" if close_val > float(df_etf['MA60'].iloc[-1] or close_val) else "↓ 下行")
        
        else:
            st.error(f"⚠️ {sector} 数据暂时不可用。请稍后重试或检查网络连接。")
            st.info("💡 提示：首次加载需要从网络获取数据，数据获取后会自动缓存到本地，后续访问将秒速加载。")

# ══════════════════════════════════════════
# 宏观三大指标
# ══════════════════════════════════════════
st.markdown("---")
st.subheader("📊 宏观经济三大脉搏 (PMI · CPI · GDP)")
st.caption("Macro Economic Indicators | 数据源：AkShare + 本地智能缓存")

tab_pmi, tab_cpi, tab_gdp = st.tabs(["🏗️ PMI 制造业", "🛒 CPI 通胀", "💹 GDP 增速"])

with tab_pmi:
    df_pmi, src = load_macro('pmi')
    if df_pmi is not None:
        if src == "demo":
            st.info("🌐 海外展示模拟数据，国内运行时将自动加载真实 PMI 数据")
        elif src == "stale_cache":
            st.info("📦 使用缓存数据")
        try:
            numeric_cols = df_pmi.select_dtypes(include='number').columns.tolist()
            date_col = [c for c in df_pmi.columns if '日期' in c or '时间' in c or '年' in c]
            if date_col and numeric_cols:
                fig_pmi = px.line(df_pmi, x=date_col[0], y=numeric_cols[0],
                                  title="中国制造业 PMI 趋势", template=PLOTLY_TEMPLATE)
                fig_pmi.update_traces(line_color='#FFD166', line_width=3)
                fig_pmi.add_hline(y=50, line_dash="dot", line_color="#FF5A5F",
                                  annotation_text="荣枯线 50")
                fig_pmi.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400)
                st.plotly_chart(fig_pmi, use_container_width=True)
            st.dataframe(df_pmi.head(15), use_container_width=True)
        except Exception:
            st.dataframe(df_pmi.head(15), use_container_width=True)
    else:
        st.warning("PMI 数据暂不可用，请稍后重试。")

with tab_cpi:
    df_cpi, src = load_macro('cpi')
    if df_cpi is not None:
        if src == "demo":
            st.info("🌐 海外展示模拟数据，国内运行时将自动加载真实 CPI 数据")
        elif src == "stale_cache":
            st.info("📦 使用缓存数据")
        try:
            numeric_cols = df_cpi.select_dtypes(include='number').columns.tolist()
            date_col = [c for c in df_cpi.columns if '日期' in c or '时间' in c or '年' in c]
            if date_col and numeric_cols:
                fig_cpi = px.line(df_cpi, x=date_col[0], y=numeric_cols[0],
                                  title="中国 CPI 趋势", template=PLOTLY_TEMPLATE)
                fig_cpi.update_traces(line_color='#00C2FF', line_width=3)
                fig_cpi.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400)
                st.plotly_chart(fig_cpi, use_container_width=True)
            st.dataframe(df_cpi.head(15), use_container_width=True)
        except Exception:
            st.dataframe(df_cpi.head(15), use_container_width=True)
    else:
        st.warning("CPI 数据暂不可用，请稍后重试。")

with tab_gdp:
    df_gdp, src = load_macro('gdp')
    if df_gdp is not None:
        if src == "demo":
            st.info("🌐 海外展示模拟数据，国内运行时将自动加载真实 GDP 数据")
        elif src == "stale_cache":
            st.info("📦 使用缓存数据")
        try:
            numeric_cols = df_gdp.select_dtypes(include='number').columns.tolist()
            date_col = [c for c in df_gdp.columns if '日期' in c or '时间' in c or '年' in c or '季' in c]
            if date_col and numeric_cols:
                fig_gdp = px.bar(df_gdp.head(30), x=date_col[0], y=numeric_cols[0],
                                 title="中国 GDP 历年增速", template=PLOTLY_TEMPLATE)
                fig_gdp.update_traces(marker_color='#2ECC71')
                fig_gdp.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400)
                st.plotly_chart(fig_gdp, use_container_width=True)
            st.dataframe(df_gdp.head(15), use_container_width=True)
        except Exception:
            st.dataframe(df_gdp.head(15), use_container_width=True)
    else:
        st.warning("GDP 数据暂不可用，请稍后重试。")

# ══════════════════════════════════════════
# 中韩产业链对比
# ══════════════════════════════════════════
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
