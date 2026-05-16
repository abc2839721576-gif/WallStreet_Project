"""
政策雷达站 + 研报智能摘要页面
功能：抓取财经新闻，TF-IDF关键词提取，SnowNLP/TextBlob双语情感分析，词云图
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import akshare as ak
import json, os, re, sys
from datetime import datetime, timedelta
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_style import inject_bloomberg_css

st.set_page_config(page_title="政策雷达 | WallStreet Hub", page_icon="📡", layout="wide")
PLOTLY_TEMPLATE = "plotly_dark"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "policies")
os.makedirs(DATA_DIR, exist_ok=True)

# ── 注入 Bloomberg Lite CSS（背景由 config.toml 控制）──
inject_bloomberg_css()

st.title("📡 政策雷达站 × 研报智能摘要")
st.caption("Policy Radar · Research Report NLP Engine | 中英双语情感分析")
st.markdown("---")

# ── 示例数据（海外服务器兜底用）────────────────────────────────
def _get_demo_news():
    """当 AkShare 数据源不可用时，返回高质量的示例财经新闻"""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    demo_data = [
        {"标题": "国务院常务会议：加大宏观政策调节力度，推动经济持续回升向好", "时间": today, "来源": "央视财经新闻", "链接": ""},
        {"标题": "央行宣布定向降准0.5个百分点，释放长期资金约1万亿元", "时间": today, "来源": "央视财经新闻", "链接": ""},
        {"标题": "工信部：加快推进新型工业化，培育壮大先进制造业集群", "时间": today, "来源": "央视财经新闻", "链接": ""},
        {"标题": "半导体行业迎来政策红利：国家集成电路产业基金三期即将落地", "时间": today, "来源": "新浪环球滚动", "链接": ""},
        {"标题": "宁德时代固态电池量产计划提前，新能源产业链全线上涨", "时间": today, "来源": "新浪环球滚动", "链接": ""},
        {"标题": "证监会发布新规：优化IPO审核流程，支持科技企业上市融资", "时间": today, "来源": "百度财经", "链接": ""},
        {"标题": "商务部：中美经贸磋商取得阶段性进展，双方同意继续对话", "时间": today, "来源": "央视财经新闻", "链接": ""},
        {"标题": "A股三大指数集体收涨，半导体板块领涨，成交额突破万亿", "时间": today, "来源": "新浪环球滚动", "链接": ""},
        {"标题": "光伏行业整合加速：多家龙头企业宣布扩产计划", "时间": yesterday, "来源": "百度财经", "链接": ""},
        {"标题": "数字人民币试点范围扩大至全国17个城市，金融科技板块走强", "时间": yesterday, "来源": "央视财经新闻", "链接": ""},
        {"标题": "国家发改委：推动新基建投资，5G基站建设目标超额完成", "时间": yesterday, "来源": "新浪环球滚动", "链接": ""},
        {"标题": "稀土管理条例正式实施，新材料板块迎来估值重塑", "时间": yesterday, "来源": "百度财经", "链接": ""},
        {"标题": "财政部：继续实施减税降费政策，预计全年减负超3万亿元", "时间": yesterday, "来源": "央视财经新闻", "链接": ""},
        {"标题": "华为发布新一代AI芯片，国产算力替代加速推进", "时间": yesterday, "来源": "新浪环球滚动", "链接": ""},
        {"标题": "银保监会：引导银行加大对制造业中长期贷款投放力度", "时间": yesterday, "来源": "百度财经", "链接": ""},
    ]
    return pd.DataFrame(demo_data)

def _get_demo_reports():
    """示例研报数据"""
    demo_reports = [
        {"股票代码": "300750", "股票名称": "宁德时代", "报告标题": "固态电池量产在即，维持买入评级", "评级": "买入", "机构": "中信证券"},
        {"股票代码": "600519", "股票名称": "贵州茅台", "报告标题": "高端白酒需求稳健，业绩超预期", "评级": "买入", "机构": "国泰君安"},
        {"股票代码": "000858", "股票名称": "五粮液", "报告标题": "渠道改革成效显现，盈利能力提升", "评级": "增持", "机构": "华泰证券"},
        {"股票代码": "002475", "股票名称": "立讯精密", "报告标题": "消费电子复苏叠加汽车业务放量", "评级": "买入", "机构": "海通证券"},
        {"股票代码": "601012", "股票名称": "隆基绿能", "报告标题": "BC电池技术领先，产能扩张加速", "评级": "增持", "机构": "招商证券"},
        {"股票代码": "688981", "股票名称": "中芯国际", "报告标题": "成熟制程需求回暖，产能利用率回升", "评级": "买入", "机构": "中金公司"},
        {"股票代码": "300059", "股票名称": "东方财富", "报告标题": "市场活跃度提升带动经纪业务增长", "评级": "买入", "机构": "广发证券"},
        {"股票代码": "002594", "股票名称": "比亚迪", "报告标题": "海外市场拓展超预期，新车型周期开启", "评级": "买入", "机构": "申万宏源"},
        {"股票代码": "603259", "股票名称": "药明康德", "报告标题": "CXO行业见底回升，订单恢复增长", "评级": "增持", "机构": "中信建投"},
        {"股票代码": "000001", "股票名称": "平安银行", "报告标题": "零售转型深化，资产质量改善", "评级": "增持", "机构": "兴业证券"},
    ]
    return pd.DataFrame(demo_reports)

# ── 数据抓取层 ────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def load_financial_news():
    """从多个AkShare接口抓取最新财经新闻 (自动降级，海外使用示例数据)"""
    all_news = []
    sources = [
        ("央视财经新闻", lambda: ak.news_cctv(date=datetime.now().strftime("%Y%m%d"))),
        ("新浪环球滚动", lambda: ak.stock_info_global_sina()),
        ("百度财经", lambda: ak.news_economic_baidu()),
    ]
    
    for source_name, func in sources:
        try:
            df = func()
            if df is not None and not df.empty:
                df['来源'] = source_name
                # 为了统一格式，新浪的可能叫 'title' 或 '标题'
                if 'title' in df.columns and '标题' not in df.columns:
                    df['标题'] = df['title']
                if 'url' in df.columns and '链接' not in df.columns:
                    df['链接'] = df['url']
                all_news.append(df)
                if source_name == "央视财经新闻" or source_name == "新浪环球滚动":
                    # 获取到一个可靠源就足够了，避免请求太慢
                    break
        except Exception:
            pass
    
    if all_news:
        combined = pd.concat(all_news, ignore_index=True)
        return combined, False  # False = 不是示例数据
    
    # 兜底：返回示例数据
    return _get_demo_news(), True  # True = 是示例数据

@st.cache_data(ttl=3600)
def load_research_reports():
    """通过 AkShare 抓取 A 股研报摘要（海外自动降级为示例数据）"""
    try:
        df = ak.stock_research_report_em(symbol="最新报告")
        return df, False
    except Exception:
        try:
            # 备用：抓取行业研报
            df = ak.stock_research_report_em(symbol="行业报告")
            return df, False
        except Exception:
            return _get_demo_reports(), True

# ── NLP 处理层 ────────────────────────────────────────────────
def extract_keywords_tfidf(texts, top_n=15):
    """用 TF-IDF 提取关键词（轻量本地实现，无需第三方 NLP 库）"""
    try:
        import jieba
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # 停用词列表
        stop_words = ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                      '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                      '自己', '这', '那', '我们', '它', '她', '他', '记者', '报道', '据', '显示', '表示',
                      '中国', '全国', '相关', '进行', '发展', '工作', '建设', '推进', '加强', '提高']
        
        # 分词
        segmented = [' '.join([w for w in jieba.cut(t) if len(w) > 1 and w not in stop_words]) 
                     for t in texts if isinstance(t, str)]
        
        if not segmented:
            return []
        
        vectorizer = TfidfVectorizer(max_features=50, min_df=1)
        tfidf_matrix = vectorizer.fit_transform(segmented)
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.sum(axis=0).A1
        
        keyword_scores = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
        return keyword_scores[:top_n]
    except ImportError:
        # 降级到简单词频
        all_text = ' '.join([str(t) for t in texts if isinstance(t, str)])
        words = [w for w in all_text.split() if len(w) > 1]
        return Counter(words).most_common(top_n)
    except Exception:
        return []

def analyze_sentiment_cn(text):
    """中文情感分析"""
    try:
        from snownlp import SnowNLP
        s = SnowNLP(str(text))
        score = s.sentiments  # 0-1, >0.5 positive
        if score > 0.65:
            return score, "📈 积极 (Positive)"
        elif score < 0.35:
            return score, "📉 消极 (Negative)"
        else:
            return score, "➡️ 中性 (Neutral)"
    except ImportError:
        return 0.5, "➡️ 中性 (NLP库未安装)"
    except Exception:
        return 0.5, "➡️ 中性 (分析失败)"

def analyze_sentiment_en(text):
    """英文情感分析"""
    try:
        from textblob import TextBlob
        blob = TextBlob(str(text))
        score = (blob.sentiment.polarity + 1) / 2  # 归一化到 0-1
        if score > 0.6:
            return score, "📈 Bullish (Positive)"
        elif score < 0.4:
            return score, "📉 Bearish (Negative)"
        else:
            return score, "➡️ Neutral"
    except ImportError:
        return 0.5, "➡️ Neutral (TextBlob not installed)"
    except Exception:
        return 0.5, "➡️ Neutral"

# ── 财经新闻雷达 ──────────────────────────────────────────────
st.subheader("📰 实时财经政策新闻")

with st.spinner("正在抓取最新财经新闻..."):
    df_news, is_demo_news = load_financial_news()

if is_demo_news:
    st.info("🌐 当前使用示例数据展示（海外服务器无法连接国内数据源）。在国内运行时将自动切换为实时新闻。")

if df_news is not None and not df_news.empty:
    # 显示新闻列表
    title_col = next((c for c in df_news.columns if '标题' in c or 'title' in c.lower()), None)
    date_col  = next((c for c in df_news.columns if '时间' in c or 'date' in c.lower() or '日期' in c), None)
    url_col   = next((c for c in df_news.columns if '链接' in c or 'url' in c.lower()), None)
    
    # 行业过滤
    industry_tags = {
        "全部": None,
        "半导体/芯片": ["半导体", "芯片", "集成电路", "光刻", "存储"],
        "新能源/电池": ["锂电", "新能源", "光伏", "储能", "电池", "CATL"],
        "新材料": ["新材料", "碳纤维", "稀土", "材料"],
        "金融/FinTech": ["金融", "银行", "基金", "债券", "数字人民币", "FinTech"],
    }
    
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        filter_industry = st.selectbox("🏷️ 按行业筛选新闻：", list(industry_tags.keys()))
    with col_f2:
        show_n = st.slider("显示条数", 5, 30, 15)
    
    df_display = df_news.copy()
    if filter_industry != "全部" and title_col:
        keywords = industry_tags[filter_industry]
        mask = df_display[title_col].apply(
            lambda x: any(kw in str(x) for kw in keywords) if isinstance(x, str) else False
        )
        df_display = df_display[mask]
    
    df_display = df_display.head(show_n)
    
    if not df_display.empty and title_col:
        for _, row in df_display.iterrows():
            title = str(row.get(title_col, ''))
            date  = str(row.get(date_col, '')) if date_col else ''
            url   = str(row.get(url_col, '')) if url_col else ''
            
            # 情感打分
            score, label = analyze_sentiment_cn(title)
            
            col_news, col_sent = st.columns([4, 1])
            with col_news:
                if url and url.startswith('http'):
                    st.markdown(f"[{title}]({url})")
                else:
                    st.markdown(f"**{title}**")
                if date:
                    st.caption(f"🕐 {date} | 来源：{row.get('来源', '')}")
            with col_sent:
                color = "#10B981" if score > 0.65 else ("#EF4444" if score < 0.35 else "#94A3B8")
                st.markdown(f"<span style='color:{color}'>{label}</span><br><small>情感分: {score:.2f}</small>", unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.info(f"没有找到与「{filter_industry}」相关的新闻，请尝试其他筛选条件。")
else:
    st.warning("暂无法获取财经新闻，请检查网络连接。")

# ── TF-IDF 关键词分析 ─────────────────────────────────────────
st.markdown("---")
st.subheader("🔑 新闻热词 TF-IDF 分析")
st.caption("Keyword Extraction via TF-IDF | 自动识别当前市场最高频的政策关键词")

if df_news is not None and not df_news.empty and title_col:
    texts = df_news[title_col].dropna().tolist()
    with st.spinner("提取 TF-IDF 关键词..."):
        keywords = extract_keywords_tfidf(texts, top_n=15)
    
    if keywords:
        kw_df = pd.DataFrame(keywords, columns=['关键词', 'TF-IDF 权重'])
        kw_df = kw_df.sort_values('TF-IDF 权重', ascending=True)
        
        fig_kw = px.bar(kw_df, x='TF-IDF 权重', y='关键词', orientation='h',
                        title="新闻关键词 TF-IDF 权重排行 (越长 = 越重要)",
                        color='TF-IDF 权重', color_continuous_scale='Teal',
                        text_auto='.3f', template=PLOTLY_TEMPLATE)
        fig_kw.update_layout(height=500)
        st.plotly_chart(fig_kw, use_container_width=True)
    else:
        st.info("关键词提取失败，请确认 jieba 和 sklearn 已安装。")

# ── 英文研报输入分析 ──────────────────────────────────────────
st.markdown("---")
st.subheader("🌐 英文研报 NLP 速读分析")
st.caption("Paste any English research report excerpt for instant NLP analysis")

sample_en = """Goldman Sachs maintains a buy rating on CATL, citing strong demand 
for EV batteries in Europe and North America. The firm raised its price target 
from HKD 280 to HKD 320, expecting revenue growth of 25% YoY driven by solid-state 
battery technology breakthroughs and new customer wins including BMW and Volkswagen."""

en_text = st.text_area("📋 粘贴英文研报内容（或使用示例）：", value=sample_en, height=150)

if st.button("🧠 一键 NLP 分析（英文）"):
    en_col1, en_col2 = st.columns(2)
    
    with en_col1:
        st.markdown("##### 📊 情感分析 (TextBlob)")
        score, label = analyze_sentiment_en(en_text)
        color = "#10B981" if score > 0.6 else ("#EF4444" if score < 0.4 else "#94A3B8")
        st.markdown(f"<h2 style='color:{color}'>{label}</h2>", unsafe_allow_html=True)
        st.metric("情感极性得分 (0-1)", f"{score:.3f}")
        st.progress(score)
    
    with en_col2:
        st.markdown("##### 🔑 关键词提取")
        # 简单英文关键词提取（无需额外库）
        stop_en = {'the', 'a', 'an', 'is', 'it', 'in', 'on', 'at', 'to', 'for', 'of',
                   'and', 'or', 'but', 'with', 'from', 'by', 'its', 'that', 'this',
                   'as', 'be', 'are', 'was', 'were', 'has', 'have', 'had', 'will'}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', en_text.lower())
        word_freq = Counter(w for w in words if w not in stop_en)
        top_words = word_freq.most_common(10)
        if top_words:
            wf_df = pd.DataFrame(top_words, columns=['Word', 'Frequency'])
            fig_en_kw = px.bar(wf_df, x='Frequency', y='Word', orientation='h',
                               color='Frequency', color_continuous_scale='Blues',
                               template=PLOTLY_TEMPLATE, height=350)
            st.plotly_chart(fig_en_kw, use_container_width=True)

# ── 研报聚合（AkShare）────────────────────────────────────────
st.markdown("---")
st.subheader("🏦 东方财富研报聚合")
st.caption("Research Report Aggregator via AkShare | A股最新机构研究报告")

with st.spinner("加载研报数据..."):
    df_reports, is_demo_reports = load_research_reports()

if is_demo_reports:
    st.info("🌐 当前使用示例研报数据展示。在国内运行时将自动加载东方财富实时研报。")

if df_reports is not None and not df_reports.empty:
    st.success(f"✅ 已加载 {len(df_reports)} 条研报记录")
    st.dataframe(df_reports.head(20), use_container_width=True)
    
    # 评级分布
    rating_col = next((c for c in df_reports.columns if '评级' in c or 'rating' in c.lower()), None)
    if rating_col:
        rating_counts = df_reports[rating_col].value_counts().reset_index()
        rating_counts.columns = ['评级', '数量']
        fig_rating = px.pie(rating_counts, values='数量', names='评级',
                            title="研报评级分布", template=PLOTLY_TEMPLATE,
                            color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig_rating, use_container_width=True)
else:
    st.info("研报接口暂时无法访问，这是正常现象（需要特定权限）。您可以在文本框中手动粘贴研报内容进行分析。")

# ── 页脚说明 ──
st.markdown("---")
st.caption("💡 提示：本页面在国内网络环境下将自动获取实时数据；海外部署时使用精选示例数据展示功能。")
