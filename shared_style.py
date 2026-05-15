"""
WallStreet Hub - 全局共享样式模块
所有页面统一调用 inject_bloomberg_css() 即可注入一致的 Bloomberg Lite 主题样式。
注意：基础暗色背景由 .streamlit/config.toml 控制，此处只负责增强样式。
"""
import streamlit as st

def inject_bloomberg_css():
    """注入 Bloomberg Lite 增强 CSS（不含背景色，背景色由 config.toml 控制）"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    
    /* ── 全局字体 ── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'HarmonyOS Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif !important;
    }
    
    /* ── 隐藏 Streamlit 默认 UI ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ── 分隔线渐变 ── */
    hr {
        border: 0;
        height: 1px;
        background: linear-gradient(to right, rgba(0,194,255,0), rgba(0,194,255,0.4), rgba(0,194,255,0));
        margin: 25px 0;
    }
    
    /* ── Metric 卡片（毛玻璃 + hover 动效） ── */
    div[data-testid="metric-container"] {
        background: rgba(19, 26, 46, 0.8);
        border: 1px solid rgba(255,255,255,0.06);
        padding: 18px 22px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        transition: all 0.25s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        border: 1px solid rgba(0,194,255,0.35);
        box-shadow: 0 8px 30px rgba(0,194,255,0.08);
    }
    
    /* ── 侧边栏导航发光 hover ── */
    [data-testid="stSidebarNav"] li a {
        transition: all 0.3s ease;
        border-left: 3px solid transparent;
        padding-left: 10px;
    }
    [data-testid="stSidebarNav"] li a:hover {
        background: linear-gradient(90deg, rgba(0,194,255,0.12) 0%, transparent 100%) !important;
        border-left: 3px solid #00C2FF;
    }
    
    /* ── Tabs 美化 ── */
    button[data-baseweb="tab"] {
        background-color: rgba(19,26,46,0.6) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        color: #94A3B8 !important;
        padding: 8px 20px !important;
        transition: all 0.2s ease !important;
        font-weight: 500 !important;
    }
    button[data-baseweb="tab"]:hover {
        background-color: rgba(29,39,66,0.8) !important;
        border-color: rgba(0,194,255,0.25) !important;
        color: #E2E8F0 !important;
    }
    button[aria-selected="true"] {
        background-color: rgba(0,194,255,0.12) !important;
        border: 1px solid #00C2FF !important;
        color: #00C2FF !important;
        box-shadow: 0 0 12px rgba(0,194,255,0.15) !important;
        font-weight: 600 !important;
    }
    /* Tab 下划线隐藏（用边框代替） */
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }
    div[data-baseweb="tab-border"] {
        display: none !important;
    }
    
    /* ── 按钮微交互 ── */
    .stButton > button {
        border-radius: 10px;
        border: 1px solid rgba(0,194,255,0.3);
        transition: all 0.25s ease;
        font-weight: 500;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,194,255,0.15);
    }
    .stButton > button:active {
        transform: scale(0.97);
    }
    
    /* ── Expander 美化 ── */
    details {
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
        background: rgba(19,26,46,0.5) !important;
    }
    
    /* ── 入场动画 class ── */
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeSlideUp 0.5s ease forwards; }
    .fade-in-delay-1 { animation: fadeSlideUp 0.5s ease 0.1s forwards; opacity: 0; }
    .fade-in-delay-2 { animation: fadeSlideUp 0.5s ease 0.2s forwards; opacity: 0; }
    .fade-in-delay-3 { animation: fadeSlideUp 0.5s ease 0.3s forwards; opacity: 0; }
    
    </style>
    """, unsafe_allow_html=True)
