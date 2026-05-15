import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os, io, time, json, requests
from sqlalchemy import create_engine
import akshare as ak
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# ==========================================
# 页面配置
# ==========================================
st.set_page_config(
    page_title="Wall Street Agent | 基金分析看板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 全局 CSS 注入
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', 'Microsoft YaHei', sans-serif; }
    div[data-testid="metric-container"] {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(148, 163, 184, 0.12);
        padding: 15px 20px; border-radius: 12px;
        box-shadow: 0 4px 30px rgba(0,0,0,0.5);
        backdrop-filter: blur(8px); transition: all 0.35s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(59, 130, 246, 0.6);
        box-shadow: 0 10px 40px rgba(59,130,246,0.12);
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    hr { border:0; height:1px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(59,130,246,0.5), rgba(0,0,0,0)); }
    </style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_dark"
DATA_DIR = "./wallstreet_data"
DB_URL = "mysql+pymysql://root:123456@localhost/finance_ai?charset=utf8mb4"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ==========================================
# 多源自动降级数据抓取引擎
# ==========================================
def _source_akshare_em(fund_code):
    """数据源 A：AkShare 东方财富接口"""
    df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
    if df is not None and not df.empty:
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values('净值日期')
        return df[['净值日期', '单位净值', '日增长率']]
    return None

def _source_eastmoney_http(fund_code):
    """数据源 B：东方财富直连 HTTP API"""
    url = f"https://api.fund.eastmoney.com/f10/lsjz"
    params = {
        'fundCode': fund_code, 'pageIndex': 1, 'pageSize': 2000,
        'startDate': '', 'endDate': ''
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://fundf10.eastmoney.com/'
    }
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    data = resp.json()
    if data.get('Data') and data['Data'].get('LSJZList'):
        records = data['Data']['LSJZList']
        rows = []
        for r in records:
            try:
                rows.append({
                    '净值日期': pd.to_datetime(r['FSRQ']),
                    '单位净值': float(r['DWJZ']),
                    '日增长率': float(r.get('JZZZL', 0) or 0)
                })
            except (ValueError, TypeError):
                continue
        if rows:
            df = pd.DataFrame(rows).sort_values('净值日期')
            return df
    return None

def _source_tiantian_http(fund_code):
    """数据源 C：天天基金网直连 HTTP API"""
    url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://fund.eastmoney.com/'
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.encoding = 'utf-8'
    text = resp.text
    # 解析 JS 变量 Data_netWorthTrend = [...]
    import re
    match = re.search(r'var\s+Data_netWorthTrend\s*=\s*(\[.*?\]);', text, re.DOTALL)
    if match:
        raw = json.loads(match.group(1))
        rows = []
        for item in raw:
            try:
                rows.append({
                    '净值日期': pd.to_datetime(item['x'], unit='ms'),
                    '单位净值': float(item['y']),
                    '日增长率': float(item.get('equityReturn', 0) or 0)
                })
            except (ValueError, TypeError, KeyError):
                continue
        if rows:
            df = pd.DataFrame(rows).sort_values('净值日期')
            return df
    return None

def fetch_fund_with_fallback(fund_code, status_callback=None):
    """
    多源自动降级抓取引擎
    按优先级依次尝试 3 个数据源，任一成功即返回。
    返回: (DataFrame, source_name) 或 (None, error_msg)
    """
    sources = [
        ('AkShare 东方财富', _source_akshare_em),
        ('东方财富 HTTP 直连', _source_eastmoney_http),
        ('天天基金 JS 解析', _source_tiantian_http),
    ]
    errors = []
    for name, func in sources:
        try:
            if status_callback:
                status_callback(f"🔄 正在尝试数据源：**{name}**...")
            time.sleep(0.5)  # 防止请求过快
            df = func(fund_code)
            if df is not None and not df.empty:
                return df, name
            else:
                errors.append(f"{name}: 返回数据为空")
        except Exception as e:
            errors.append(f"{name}: {str(e)[:100]}")
    return None, '\n'.join(errors)

# ==========================================
# 数据加载函数
# ==========================================
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    df['净值日期'] = pd.to_datetime(df['净值日期'])
    df = df.sort_values('净值日期')
    df['日收益率(%)'] = df['单位净值'].pct_change() * 100
    first_nav = df['单位净值'].iloc[0]
    df['累计收益率(%)'] = ((df['单位净值'] - first_nav) / first_nav) * 100
    df['历史最高净值'] = df['单位净值'].cummax()
    df['回撤幅度(%)'] = ((df['单位净值'] - df['历史最高净值']) / df['历史最高净值']) * 100
    return df

@st.cache_data(ttl=60)
def load_market_indices():
    try:
        df = ak.stock_zh_index_spot_sina()
        return df[df['名称'].isin(['上证指数', '深证成指', '创业板指', '沪深300'])]
    except:
        return None

@st.cache_data
def load_holdings_from_db(fund_code):
    try:
        engine = create_engine(DB_URL)
        q = f"SELECT `股票代码`,`股票简称`,`持股数量(万股)`,`持股总市值(万元)`,`持股市值占基金净值比(%)`,`报告期` FROM fund_holdings_2019 WHERE `代码`='{fund_code}.OF' ORDER BY `持股市值占基金净值比(%)` DESC"
        return pd.read_sql(q, con=engine)
    except:
        return None

def compute_risk_metrics(df):
    """计算单只基金的风险指标"""
    daily_ret = df['单位净值'].pct_change().dropna()
    annual_ret = (df['单位净值'].iloc[-1] / df['单位净值'].iloc[0]) ** (252 / len(df)) - 1
    annual_vol = daily_ret.std() * np.sqrt(252)
    sharpe = annual_ret / annual_vol if annual_vol != 0 else 0
    max_dd = df['回撤幅度(%)'].min()
    calmar = (annual_ret * 100) / abs(max_dd) if max_dd != 0 else 0
    sortino_downside = daily_ret[daily_ret < 0].std() * np.sqrt(252)
    sortino = annual_ret / sortino_downside if sortino_downside != 0 else 0
    return {
        '年化收益率': round(annual_ret * 100, 2),
        '年化波动率': round(annual_vol * 100, 2),
        '夏普比率': round(sharpe, 2),
        '最大回撤': round(abs(max_dd), 2),
        '卡尔玛比率': round(calmar, 2),
        '索提诺比率': round(sortino, 2),
    }

@st.cache_data
def load_holdings_yoy(fund_code):
    """从 MySQL 联合查询 2018/2019 重仓数据做同比分析"""
    try:
        engine = create_engine(DB_URL)
        full_code = f"{fund_code}.OF"
        q18 = f"SELECT `股票简称`,`持股总市值(万元)` as `2018市值` FROM fund_holdings_2018 WHERE `代码`='{full_code}' ORDER BY `持股市值占基金净值比(%)` DESC LIMIT 10"
        q19 = f"SELECT `股票简称`,`持股总市值(万元)` as `2019市值` FROM fund_holdings_2019 WHERE `代码`='{full_code}' ORDER BY `持股市值占基金净值比(%)` DESC LIMIT 10"
        df18 = pd.read_sql(q18, con=engine)
        df19 = pd.read_sql(q19, con=engine)
        merged = pd.merge(df19, df18, on='股票简称', how='outer').fillna(0)
        merged['变动(万元)'] = merged['2019市值'] - merged['2018市值']
        merged['变动方向'] = merged['变动(万元)'].apply(lambda x: '增持' if x > 0 else ('减持' if x < 0 else '持平'))
        return merged
    except:
        return None

def predict_nav(df, days=30):
    """使用线性回归 + 移动平均做净值趋势预测"""
    df_pred = df[['净值日期', '单位净值']].copy()
    df_pred['day_num'] = (df_pred['净值日期'] - df_pred['净值日期'].min()).dt.days
    # 线性回归
    X = df_pred['day_num'].values.reshape(-1, 1)
    y = df_pred['单位净值'].values
    model = LinearRegression().fit(X, y)
    # 未来日期
    last_day = df_pred['day_num'].max()
    future_days = np.arange(last_day + 1, last_day + days + 1).reshape(-1, 1)
    future_dates = pd.date_range(df_pred['净值日期'].max() + pd.Timedelta(days=1), periods=days)
    pred_values = model.predict(future_days)
    # 移动平均 (MA20)
    ma20 = df_pred['单位净值'].rolling(window=20).mean()
    # 置信区间 (基于历史波动率)
    hist_vol = df_pred['单位净值'].pct_change().std()
    upper = pred_values * (1 + 1.96 * hist_vol * np.sqrt(np.arange(1, days+1)))
    lower = pred_values * (1 - 1.96 * hist_vol * np.sqrt(np.arange(1, days+1)))
    return {
        'hist_dates': df_pred['净值日期'], 'hist_nav': df_pred['单位净值'], 'ma20': ma20,
        'future_dates': future_dates, 'pred': pred_values, 'upper': upper, 'lower': lower,
        'r2': round(model.score(X, y), 4), 'slope': round(model.coef_[0] * 252, 4)
    }

# ==========================================
# 侧边栏
# ==========================================
st.sidebar.title("🤖 华尔街 Agent")
st.sidebar.markdown("---")

# --- 实时抓取 ---
st.sidebar.subheader("📡 实时数据抓取")
new_fund_code = st.sidebar.text_input("输入 6 位基金代码", max_chars=6)
if st.sidebar.button("🔄 一键拉取最新净值"):
    if new_fund_code and len(new_fund_code) == 6:
        with st.sidebar.status(f"正在请求 {new_fund_code}（多源自动降级）...", expanded=True) as status:
            status_log = st.empty()
            def update_status(msg):
                status_log.write(msg)

            fund_data, source_or_error = fetch_fund_with_fallback(new_fund_code, update_status)

            if fund_data is not None:
                fund_data.to_csv(
                    os.path.join(DATA_DIR, f"fund_{new_fund_code}_history.csv"),
                    index=False, encoding='utf-8-sig'
                )
                status.update(label=f"✅ 抓取成功！", state="complete")
                st.success(
                    f"✅ 基金 **{new_fund_code}** 数据拉取成功！\n\n"
                    f"📊 共 **{len(fund_data)}** 条记录\n\n"
                    f"🔗 数据源：**{source_or_error}**"
                )
                st.rerun()
            else:
                status.update(label="❌ 全部数据源均失败", state="error")
                st.error(
                    f"🚫 基金 {new_fund_code} 三个数据源均无法获取数据。\n\n"
                    f"**失败详情：**\n{source_or_error}\n\n"
                    "💡 **建议：** 确认基金代码是否正确，或等待 1 分钟后重试。"
                )
    else:
        st.sidebar.warning("请输入正确的 6 位代码！")

st.sidebar.markdown("---")

# --- 数据源选择 ---
csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith("_history.csv")]
if not csv_files:
    st.sidebar.error("暂无数据，请先抓取！"); st.stop()

selected_file = st.sidebar.selectbox("📂 选择基金：", csv_files,
    format_func=lambda x: x.replace("fund_","").replace("_history.csv",""))
file_path = os.path.join(DATA_DIR, selected_file)
fund_code = selected_file.replace("fund_","").replace("_history.csv","")

# --- 开发者名片 ---
st.sidebar.markdown("---")
st.sidebar.subheader("👨‍💻 关于开发者")
st.sidebar.info(
    "**张君瑞 (Zhang Junrui)**\n\n"
    "🎓 **青岛大学** | 理工+金融复合背景\n\n"
    "💼 **求职意向**：数据分析师\n\n"
    "📧 [联系邮箱](mailto:2839721576@qq.com)\n\n"
    "---\n*Powered by Wall Street Agent*"
)

# ==========================================
# 主体看板
# ==========================================
st.title(f"📊 基金 {fund_code} 深度分析看板")
st.caption("Steward Agent & Wall Street Agent 联合打造 | API 实时数据 + MySQL 数据库 + 量化分析引擎")

# --- 大盘行情 ---
st.subheader("🌍 实时大盘行情")
market_df = load_market_indices()
if market_df is not None and not market_df.empty:
    cols = st.columns(len(market_df))
    for i, (_, row) in enumerate(market_df.iterrows()):
        with cols[i]:
            st.metric(label=row.get('名称',''), value=f"{row.get('最新价',0):.2f}",
                      delta=f"{row.get('涨跌幅',0):.2f}%", delta_color="inverse")
else:
    st.warning("⚠️ 暂无法获取大盘数据。")
st.markdown("---")

# --- 加载当前基金数据 ---
df_nav = load_data(file_path)
df_holdings = load_holdings_from_db(fund_code)

if df_nav is None or df_nav.empty:
    st.error("数据加载失败。"); st.stop()

# --- KPI 卡片 ---
latest_date = df_nav['净值日期'].iloc[-1].strftime('%Y-%m-%d')
latest_nav = df_nav['单位净值'].iloc[-1]
total_return = df_nav['累计收益率(%)'].iloc[-1]
max_drawdown = df_nav['回撤幅度(%)'].min()
risk = compute_risk_metrics(df_nav)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("最新净值日期", latest_date)
c2.metric("当前单位净值", f"¥ {latest_nav:.4f}")
c3.metric("累计收益率", f"{total_return:.2f}%")
c4.metric("最大回撤", f"{max_drawdown:.2f}%")
c5.metric("夏普比率", f"{risk['夏普比率']}")

st.markdown("---")


# --- 🤖 AI 智能洞察 (Auto Insight) ---
st.markdown("### 🤖 WallStreet Agent 智能洞察")
insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    st.info("💡 **趋势与风险监测**\n\n" + 
            f"- **当前趋势**：该基金累计收益率为 {total_return:.2f}%。近 20 日波动率为 {risk['年化波动率']:.2f}%，最大回撤 {max_drawdown:.2f}%。" +
            ("\n- ⚠️ **风险警示**：最大回撤较高，体现了较强的下行风险，建议谨慎追高。" if max_drawdown < -20 else "\n- ✅ **回撤控制**：最大回撤控制良好，体现了基金经理优秀的防守能力。")
    )
with insight_col2:
    if len(df_nav) > 60:
        ma20_bias = df_nav['单位净值'].iloc[-1] / df_nav['单位净值'].rolling(20).mean().iloc[-1] - 1
        st.success("🎯 **量化归因发现**\n\n" +
                f"- **MA20 偏离度**：当前价格相对 20 日均线偏离 {ma20_bias*100:.2f}%。" +
                ("\n- 📈 处于均线上方的多头趋势，有较强支撑。" if ma20_bias > 0 else "\n- 📉 跌破均线支撑，短期有回调压力，可关注后续企稳信号。")
        )
    else:
        st.warning("🎯 **量化归因发现**\n\n数据量不足 60 天，无法生成深度归因报告。")
st.markdown("---")

# ==========================================
# 六大功能 Tabs
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📉 净值走势",
    "🏦 重仓股透视",
    "📐 风险 & 组合",
    "🔮 智能预测",
    "🔗 多维数据融合",
    "🧬 深度挖掘",
    "📥 数据导出"
])

# ========== TAB 1: 净值分析 ==========
with tab1:
    st.subheader("📈 单位净值历史走势")
    fig1 = px.line(df_nav, x='净值日期', y='单位净值',
                   title=f"基金 {fund_code} 单位净值走势", template=PLOTLY_TEMPLATE)
    fig1.update_traces(line_color='#3B82F6')
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("📉 动态回撤幅度")
    fig2 = px.area(df_nav, x='净值日期', y='回撤幅度(%)',
                   title="历史动态回撤 (风险监测)", color_discrete_sequence=['#06B6D4'])
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("🔍 查看原始数据"):
        st.dataframe(df_nav.sort_values('净值日期', ascending=False), use_container_width=True)

# ========== TAB 2: 重仓股 ==========
with tab2:
    if df_holdings is not None and not df_holdings.empty:
        st.subheader("💼 核心重仓股票池 (Top 10)")
        fig3 = px.bar(df_holdings.head(10), x='股票简称', y='持股市值占基金净值比(%)',
                      color='持股市值占基金净值比(%)', color_continuous_scale="Blues",
                      text_auto='.2f', title="前十大重仓股占比 (%)")
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("🌳 资产分布树状图")
        fig4 = px.treemap(df_holdings, path=['股票简称'], values='持股总市值(万元)',
                          color='持股市值占基金净值比(%)', color_continuous_scale='Blues',
                          title="重仓股持仓市值规模分布图")
        st.plotly_chart(fig4, use_container_width=True)

        with st.expander("📊 查看 MySQL 底层数据"):
            st.dataframe(df_holdings, use_container_width=True)
    else:
        st.info(f"数据库中暂未找到 {fund_code}.OF 的重仓数据。")

# ========== TAB 3: 风险雷达 & 组合构建 ==========
with tab3:
    col_left, col_right = st.columns(2)

    # ---- 左侧：风险雷达 ----
    with col_left:
        st.subheader("🎯 风险指标雷达图")
        categories = list(risk.keys())
        # 归一化到 0-100 分，方便雷达图展示
        norm_map = {'年化收益率': 200, '年化波动率': 50, '夏普比率': 3, '最大回撤': 80, '卡尔玛比率': 3, '索提诺比率': 5}
        scores = [min(abs(risk[k]) / norm_map[k] * 100, 100) for k in categories]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor='rgba(59,130,246,0.15)',
            line=dict(color='#3B82F6', width=2),
            name=fund_code
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor='rgba(0,0,0,0)',
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, gridcolor='rgba(148,163,184,0.15)'),
                angularaxis=dict(gridcolor='rgba(148,163,184,0.15)')
            ),
            showlegend=False, template=PLOTLY_TEMPLATE,
            margin=dict(l=60, r=60, t=40, b=40), height=400
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # 风险指标详情卡片
        st.markdown("##### 📋 风险指标明细")
        risk_df = pd.DataFrame([risk], index=[fund_code]).T
        risk_df.columns = ['数值']
        st.dataframe(risk_df, use_container_width=True)

    # ---- 右侧：组合构建器 ----
    with col_right:
        st.subheader("🏗️ 组合构建器 (Portfolio Builder)")
        available_funds = [f.replace("fund_","").replace("_history.csv","") for f in csv_files]
        selected_funds = st.multiselect("选择基金 (至少 2 只)：", available_funds, default=[fund_code])

        if len(selected_funds) >= 2:
            # 权重滑块
            st.markdown("##### ⚖️ 调整权重")
            weights = {}
            remaining = 100
            for i, fc in enumerate(selected_funds):
                if i == len(selected_funds) - 1:
                    w = remaining
                    st.slider(f"{fc} 权重 (%)", 0, 100, w, key=f"w_{fc}", disabled=True)
                else:
                    w = st.slider(f"{fc} 权重 (%)", 0, remaining, remaining // (len(selected_funds) - i), key=f"w_{fc}")
                    remaining -= w
                weights[fc] = w / 100.0

            # 计算组合净值
            dfs = {}
            for fc in selected_funds:
                fp = os.path.join(DATA_DIR, f"fund_{fc}_history.csv")
                if os.path.exists(fp):
                    d = load_data(fp)
                    d = d.set_index('净值日期')[['单位净值']]
                    d.columns = [fc]
                    # 归一化为 1
                    d[fc] = d[fc] / d[fc].iloc[0]
                    dfs[fc] = d

            if len(dfs) == len(selected_funds):
                combined = pd.concat(dfs.values(), axis=1, join='inner')
                combined['组合净值'] = sum(combined[fc] * weights[fc] for fc in selected_funds)

                fig_port = go.Figure()
                for fc in selected_funds:
                    fig_port.add_trace(go.Scatter(x=combined.index, y=combined[fc],
                                                  mode='lines', name=fc, opacity=0.5,
                                                  line=dict(width=1)))
                fig_port.add_trace(go.Scatter(x=combined.index, y=combined['组合净值'],
                                              mode='lines', name='📊 组合', line=dict(color='#3B82F6', width=3)))
                fig_port.update_layout(title="组合 vs 单基金归一化走势", template=PLOTLY_TEMPLATE,
                                       yaxis_title="归一化净值", height=400,
                                       margin=dict(l=20, r=20, t=50, b=30))
                st.plotly_chart(fig_port, use_container_width=True)

                # 组合风险
                port_ret = combined['组合净值'].pct_change().dropna()
                port_annual_ret = (combined['组合净值'].iloc[-1] / combined['组合净值'].iloc[0]) ** (252/len(combined)) - 1
                port_vol = port_ret.std() * np.sqrt(252)
                port_sharpe = port_annual_ret / port_vol if port_vol != 0 else 0
                port_max_dd = ((combined['组合净值'] / combined['组合净值'].cummax()) - 1).min()

                pc1, pc2, pc3, pc4 = st.columns(4)
                pc1.metric("组合年化收益", f"{port_annual_ret*100:.2f}%")
                pc2.metric("组合年化波动", f"{port_vol*100:.2f}%")
                pc3.metric("组合夏普比率", f"{port_sharpe:.2f}")
                pc4.metric("组合最大回撤", f"{port_max_dd*100:.2f}%")
            else:
                st.warning("部分基金数据缺失，请先抓取。")
        else:
            st.info("💡 请在上方选择至少 **2 只基金** 来构建投资组合并对比。")

    st.markdown("---")
    st.subheader("🔗 基金池相关性热力图与对冲推荐")
    st.markdown("分析本地基金池中各基金日收益率的皮尔逊相关系数，寻找低相关或负相关标的以对冲风险。")
    
    if len(csv_files) >= 2:
        corr_dfs = {}
        for fc in csv_files:
            fcode = fc.replace("fund_","").replace("_history.csv","")
            fpath = os.path.join(DATA_DIR, fc)
            d = load_data(fpath)
            d = d.set_index('净值日期')[['日收益率(%)']]
            d.columns = [fcode]
            corr_dfs[fcode] = d
        
        # 合并所有基金的日收益率并计算相关性
        df_all_returns = pd.concat(corr_dfs.values(), axis=1, join='inner')
        if not df_all_returns.empty and len(df_all_returns.columns) > 1:
            corr_matrix = df_all_returns.corr()
            
            # 画热力图
            fig_corr = px.imshow(corr_matrix, text_auto=".2f", aspect="auto", 
                                color_continuous_scale='RdBu_r', 
                                title="基金日收益率相关性矩阵 (Pearson Correlation)")
            fig_corr.update_layout(template=PLOTLY_TEMPLATE, height=450)
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # 对冲推荐逻辑
            st.markdown("##### 🛡️ 智能对冲推荐")
            if fund_code in corr_matrix.columns and len(corr_matrix.columns) > 1:
                corr_with_current = corr_matrix[fund_code].drop(fund_code)
                best_hedge = corr_with_current.idxmin()
                best_hedge_val = corr_with_current.min()
                if best_hedge_val < 0.3:
                    hedge_type = "负相关" if best_hedge_val < 0 else "低相关"
                    st.success(f"**分析发现**：当前基金 ({fund_code}) 与基金 **{best_hedge}** 呈现 **{hedge_type}** (相关系数: {best_hedge_val:.2f})。\n\n"
                               f"💡 **建议**：在投资组合中配置一定比例的 {best_hedge}，可有效对冲 {fund_code} 的同向波动风险，提高夏普比率。")
                else:
                    st.info(f"本地基金池中，与 {fund_code} 相关性最低的基金是 **{best_hedge}** (相关系数: {best_hedge_val:.2f})，但它们仍呈较强正相关，对冲效果有限。建议在侧边栏抓取一些不同板块（如债券、黄金）的基金数据。")
        else:
            st.warning("合并收益率数据失败，请检查各基金的日期是否有重叠。")
    else:
        st.info("💡 请在侧边栏抓取至少 2 只基金以生成相关性热力图。")

# ========== TAB 7: 数据导出中心 ==========
with tab7:
    st.subheader("📥 数据导出中心")
    st.markdown("将看板中的分析结果一键导出为 **Excel / CSV** 文件，方便归档或分享。")

    ex1, ex2, ex3 = st.columns(3)

    with ex1:
        st.markdown("##### 📄 净值数据")
        csv_buf = df_nav.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("⬇️ 下载 CSV", data=csv_buf,
                           file_name=f"fund_{fund_code}_nav.csv", mime="text/csv")

        excel_buf = io.BytesIO()
        df_nav.to_excel(excel_buf, index=False, engine='openpyxl')
        st.download_button("⬇️ 下载 Excel", data=excel_buf.getvalue(),
                           file_name=f"fund_{fund_code}_nav.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with ex2:
        st.markdown("##### 📊 重仓股数据")
        if df_holdings is not None and not df_holdings.empty:
            h_csv = df_holdings.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("⬇️ 下载 CSV", data=h_csv,
                               file_name=f"fund_{fund_code}_holdings.csv", mime="text/csv", key="h_csv")
            h_buf = io.BytesIO()
            df_holdings.to_excel(h_buf, index=False, engine='openpyxl')
            st.download_button("⬇️ 下载 Excel", data=h_buf.getvalue(),
                               file_name=f"fund_{fund_code}_holdings.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="h_xl")
        else:
            st.info("暂无重仓股数据可导出。")

    with ex3:
        st.markdown("##### 📐 风险分析报告")
        risk_export = pd.DataFrame([risk], index=[fund_code]).T
        risk_export.columns = ['数值']
        r_buf = io.BytesIO()
        risk_export.to_excel(r_buf, engine='openpyxl')
        st.download_button("⬇️ 下载 Excel", data=r_buf.getvalue(),
                           file_name=f"fund_{fund_code}_risk_report.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="r_xl")

# ========== TAB 5: 智能预测 ==========
with tab4:
    st.subheader("🔮 净值趋势智能预测 (Linear Regression + Confidence Band)")
    pred_days = st.slider("选择预测天数", 7, 90, 30, key="pred_slider")
    result = predict_nav(df_nav, days=pred_days)

    fig_pred = go.Figure()
    # 历史净值
    fig_pred.add_trace(go.Scatter(x=result['hist_dates'], y=result['hist_nav'],
                                   mode='lines', name='历史净值', line=dict(color='#3B82F6', width=2)))
    # MA20
    fig_pred.add_trace(go.Scatter(x=result['hist_dates'], y=result['ma20'],
                                   mode='lines', name='MA20 均线', line=dict(color='#8B5CF6', width=1, dash='dot')))
    # 预测线
    fig_pred.add_trace(go.Scatter(x=result['future_dates'], y=result['pred'],
                                   mode='lines', name=f'{pred_days}日预测', line=dict(color='#06B6D4', width=2, dash='dash')))
    # 置信区间
    fig_pred.add_trace(go.Scatter(x=result['future_dates'], y=result['upper'],
                                   mode='lines', name='上界 (95%)', line=dict(width=0), showlegend=False))
    fig_pred.add_trace(go.Scatter(x=result['future_dates'], y=result['lower'],
                                   mode='lines', name='95% 置信区间', fill='tonexty',
                                   fillcolor='rgba(6,182,212,0.12)', line=dict(width=0)))
    fig_pred.update_layout(template=PLOTLY_TEMPLATE, title=f"基金 {fund_code} 未来 {pred_days} 日净值预测",
                            yaxis_title='单位净值', height=500, margin=dict(l=20,r=20,t=50,b=30))
    st.plotly_chart(fig_pred, use_container_width=True)

    # 模型指标
    m1, m2, m3 = st.columns(3)
    m1.metric("模型 R² 拟合度", f"{result['r2']}")
    m2.metric("年化斜率 (趋势)", f"{result['slope']}")
    trend = '📈 上行趋势' if result['slope'] > 0 else '📉 下行趋势'
    m3.metric("趋势判断", trend)

    st.caption("⚠️ 本预测基于线性回归与历史波动率，仅供学术参考，不构成任何投资建议。")

# ========== TAB 6: 多维数据融合 ==========
with tab5:
    st.subheader("🔗 多维数据融合分析 (2018 vs 2019 持仓同比)")
    df_yoy = load_holdings_yoy(fund_code)
    if df_yoy is not None and not df_yoy.empty:
        # 年度对比柱状图
        fig_yoy = go.Figure()
        fig_yoy.add_trace(go.Bar(name='2018 持仓市值', x=df_yoy['股票简称'], y=df_yoy['2018市值'],
                                  marker_color='rgba(148,163,184,0.6)'))
        fig_yoy.add_trace(go.Bar(name='2019 持仓市值', x=df_yoy['股票简称'], y=df_yoy['2019市值'],
                                  marker_color='#3B82F6'))
        fig_yoy.update_layout(barmode='group', template=PLOTLY_TEMPLATE,
                               title='重仓股年度持仓市值对比 (万元)', height=450)
        st.plotly_chart(fig_yoy, use_container_width=True)

        # 增减持分析
        st.subheader("📊 增减持变动分析")
        col_inc, col_dec = st.columns(2)
        inc = df_yoy[df_yoy['变动方向'] == '增持'].sort_values('变动(万元)', ascending=False)
        dec = df_yoy[df_yoy['变动方向'] == '减持'].sort_values('变动(万元)')
        with col_inc:
            st.markdown("##### 🟢 增持标的")
            if not inc.empty:
                fig_inc = px.bar(inc, x='股票简称', y='变动(万元)', color_discrete_sequence=['#10B981'], text_auto='.0f')
                fig_inc.update_layout(template=PLOTLY_TEMPLATE, height=300, margin=dict(l=10,r=10,t=30,b=10))
                st.plotly_chart(fig_inc, use_container_width=True)
            else:
                st.info("无增持数据")
        with col_dec:
            st.markdown("##### 🔴 减持标的")
            if not dec.empty:
                fig_dec = px.bar(dec, x='股票简称', y='变动(万元)', color_discrete_sequence=['#EF4444'], text_auto='.0f')
                fig_dec.update_layout(template=PLOTLY_TEMPLATE, height=300, margin=dict(l=10,r=10,t=30,b=10))
                st.plotly_chart(fig_dec, use_container_width=True)
            else:
                st.info("无减持数据")

        with st.expander("📋 查看完整同比数据"):
            st.dataframe(df_yoy, use_container_width=True)
    else:
        st.info(f"数据库中暂无 {fund_code} 的 2018/2019 双年度重仓数据可供对比。")

# ========== TAB 6: 深度数据挖掘 ==========
with tab6:
    st.subheader("🧬 深度数据挖掘 (Machine Learning & Data Mining)")
    
    st.markdown("### 1. 基金池无监督聚类分析 (K-Means Clustering)")
    st.markdown("基于本地所有基金的历史表现（年化收益率 vs 年化波动率），自动识别隐藏的投资风格。")
    
    # Run clustering on available CSV files
    if len(csv_files) >= 3:
        cluster_data = []
        for fc in csv_files:
            fp = os.path.join(DATA_DIR, fc)
            d = load_data(fp)
            if len(d) > 30: # Ensure enough data points
                r = compute_risk_metrics(d)
                fcode = fc.replace("fund_","").replace("_history.csv","")
                cluster_data.append({
                    '基金代码': fcode,
                    '年化收益率': r['年化收益率'],
                    '年化波动率': r['年化波动率']
                })
        
        if len(cluster_data) >= 3:
            df_cluster = pd.DataFrame(cluster_data)
            X_cluster = df_cluster[['年化波动率', '年化收益率']]
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_cluster)
            
            n_clusters = min(4, len(df_cluster)) # 3 or 4 clusters based on data size
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df_cluster['聚类标签'] = kmeans.fit_predict(X_scaled)
            df_cluster['聚类标签'] = df_cluster['聚类标签'].astype(str)
            
            fig_cluster = px.scatter(df_cluster, x='年化波动率', y='年化收益率', color='聚类标签',
                                     text='基金代码', title="基金投资风格聚类散点图 (Smart Beta 识别)",
                                     template=PLOTLY_TEMPLATE, size_max=15)
            fig_cluster.update_traces(textposition='top center', marker=dict(size=12))
            st.plotly_chart(fig_cluster, use_container_width=True)
            
            with st.expander("🔍 查看聚类底层数据"):
                st.dataframe(df_cluster, use_container_width=True)
        else:
            st.info("符合数据量的基金不足3只，无法进行聚类。")
    else:
        st.info("💡 本地基金池数据不足，请在左侧侧边栏至少抓取 3 只以上的基金数据来启用聚类分析。")

    st.markdown("---")
    
    st.markdown("### 2. 收益归因与因子重要性 (Random Forest Feature Importance)")
    st.markdown("利用随机森林模型，评估哪些技术因子（动量、波动、均线偏离等）对预测未来5天收益率影响最大。")
    
    # Feature Engineering for Random Forest
    df_rf = df_nav.copy()
    if len(df_rf) > 60:
        # Construct Features
        df_rf['未来5日收益率'] = df_rf['单位净值'].shift(-5) / df_rf['单位净值'] - 1
        df_rf['过去5日动量'] = df_rf['单位净值'] / df_rf['单位净值'].shift(5) - 1
        df_rf['过去20日动量'] = df_rf['单位净值'] / df_rf['单位净值'].shift(20) - 1
        df_rf['MA20偏离度'] = df_rf['单位净值'] / df_rf['单位净值'].rolling(20).mean() - 1
        df_rf['20日历史波动率'] = df_rf['日收益率(%)'].rolling(20).std()
        
        df_rf = df_rf.dropna()
        
        features = ['过去5日动量', '过去20日动量', 'MA20偏离度', '20日历史波动率']
        X_rf = df_rf[features]
        y_rf = df_rf['未来5日收益率']
        
        rf_model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
        rf_model.fit(X_rf, y_rf)
        
        importance = rf_model.feature_importances_
        df_importance = pd.DataFrame({'因子': features, '重要性权重': importance})
        df_importance = df_importance.sort_values('重要性权重', ascending=True)
        
        fig_rf = px.bar(df_importance, x='重要性权重', y='因子', orientation='h',
                        title=f"基金 {fund_code} 短期收益预测因子归因",
                        color='重要性权重', color_continuous_scale='Teal', text_auto='.3f')
        fig_rf.update_layout(template=PLOTLY_TEMPLATE, height=400)
        st.plotly_chart(fig_rf, use_container_width=True)
        
        st.caption("注：权重越高的因子，说明在随机森林模型预测该基金未来5天走势时，发挥的作用越大。该归因分析可辅助量化选基策略。")
    else:
        st.warning("该基金历史数据不足 60 天，无法运行随机森林归因模型。")
