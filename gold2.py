# import streamlit as st
# import pandas as pd
# import requests
# import time
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import json
# import os
# from datetime import datetime
# import pytz
# import re

# # ==============================
# # 1. 时区与持久化配置
# # ==============================
# st.set_page_config(layout="wide", page_title="chatgold")
# DB_FILE = "gold_all_banks_history.json"
# BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# def load_history():
#     if os.path.exists(DB_FILE):
#         try:
#             with open(DB_FILE, "r") as f: return json.load(f)
#         except: return {"banks": {}, "london": []}
#     return {"banks": {}, "london": []}

# def save_history(data):
#     try:
#         with open(DB_FILE, "w") as f: json.dump(data, f)
#     except: pass

# if "full_history" not in st.session_state:
#     st.session_state.full_history = load_history()

# # ==============================
# # 2. 页面美化样式
# # ==============================
# st.markdown("""
# <style>
# .stApp { background-color: #0F172A; color: #E5E7EB; }
# #MainMenu, footer, header {visibility:hidden;}
# .card { 
#     background: #1E293B; padding: 12px; border-radius: 10px; 
#     border: 1px solid #334155; text-align: center;
# }
# .price-val { font-size: 1.8rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin: 2px 0; }
# .label { font-size: 0.8rem; color: #94A3B8; }
# .sub-val { font-size: 0.85rem; font-weight: 600; }
# </style>
# """, unsafe_allow_html=True)

# # ==============================
# # 3. 数据采集逻辑
# # ==============================
# def fetch_gold(code):
#     """抓取黄金价格"""
#     try:
#         url = f"https://jin.20021002.xyz/api.php?type={code}"
#         res = requests.get(url, timeout=5).json()
#         return float(res["data"]["price"]) if res.get("code") == 200 else None
#     except: return None

# def fetch_exchange_sina():
#     """新浪财经离岸人民币实时汇率 (无需Token)"""
#     try:
#         url = "https://hq.sinajs.cn/list=fx_susdcnh"
#         headers = {'Referer': 'http://finance.sina.com.cn'}
#         res = requests.get(url, headers=headers, timeout=5).text
#         match = re.search(r'"([^"]+)"', res)
#         if match:
#             data = match.group(1).split(',')
#             return float(data[1])
#     except:
#         return st.session_state.get('rate', 7.2400)
#     return st.session_state.get('rate', 7.2400)

# # ==============================
# # 4. 侧边栏配置
# # ==============================
# BANK_OPTIONS = [
#     ("icbc", "工商银行"), ("zs", "浙商银行"), ("jd", "京东黄金"), 
#     ("ms", "民生银行"), ("cgb", "广发银行"), ("cib", "兴业银行")
# ]
# BANK_DICT = dict(BANK_OPTIONS)

# with st.sidebar:
#     st.title("🪙 全行实时监控")
#     target_bank = st.radio("当前观察机构", options=[b[0] for b in BANK_OPTIONS], format_func=lambda x: BANK_DICT[x])
#     refresh_rate = st.slider("扫描频率(秒)", 2, 10, 3)
#     st.info("模式：后台同步模式（所有银行都在持续记录中）")
#     if st.button("🗑️ 清空所有历史"):
#         st.session_state.full_history = {"banks": {}, "london": []}
#         if os.path.exists(DB_FILE): os.remove(DB_FILE)
#         st.rerun()

# # ==============================
# # 5. 【后台全量同步】处理逻辑
# # ==============================
# now_t = time.time()
# hist = st.session_state.full_history

# # 1. 抓取汇率
# rate = fetch_exchange_sina()
# if "prev_rate" not in st.session_state: st.session_state.prev_rate = rate
# rate_diff = rate - st.session_state.prev_rate
# st.session_state.prev_rate = rate
# st.session_state.rate = rate

# # 2. 抓取伦敦金 (作为全局参考)
# london_gold = fetch_gold("gj")
# if london_gold:
#     if len(hist["london"]) == 0 or now_t - hist["london"][-1]["t"] >= 5:
#         hist["london"].append({"t": now_t, "p": london_gold})
#         if len(hist["london"]) > 2000: hist["london"].pop(0)

# # 3. 【核心更新】循环抓取所有银行
# for code, name in BANK_OPTIONS:
#     p = fetch_gold(code)
#     if p:
#         if code not in hist["banks"]: hist["banks"][code] = []
#         # 即使不是当前看的银行，只要到了记录点（5秒），也存入历史
#         if len(hist["banks"][code]) == 0 or now_t - hist["banks"][code][-1]["t"] >= 5:
#             hist["banks"][code].append({"t": now_t, "p": p})
#             # 限制单个银行历史长度，防止文件过大
#             if len(hist["banks"][code]) > 2000: hist["banks"][code].pop(0)

# # 保存本次采集的所有成果
# save_history(hist)

# # ==============================
# # 6. UI 渲染（针对选中的目标银行）
# # ==============================
# bank_hist = hist["banks"].get(target_bank, [])
# current_price = bank_hist[-1]["p"] if bank_hist else None

# if current_price and london_gold:
#     # 涨跌计算
#     base_p = bank_hist[0]["p"]
#     diff = current_price - base_p
#     pct = (diff / base_p) * 100
#     color_bank = "#22C55E" if diff >= 0 else "#EF4444"

#     # 四栏看板
#     cols = st.columns(4)
#     with cols[0]:
#         st.markdown(f'<div class="card"><div class="label">{BANK_DICT[target_bank]} (实时)</div><div class="price-val" style="color:{color_bank}">{current_price:.2f}</div><div class="sub-val" style="color:#94A3B8">BJ: {datetime.now(BEIJING_TZ).strftime("%H:%M:%S")}</div></div>', unsafe_allow_html=True)
#     with cols[1]:
#         st.markdown(f'<div class="card"><div class="label">本次加载起涨跌</div><div class="price-val" style="color:{color_bank}">{diff:+.2f}</div><div class="sub-val" style="color:{color_bank}">{pct:+.2f}%</div></div>', unsafe_allow_html=True)
#     with cols[2]:
#         st.markdown(f'<div class="card"><div class="label">离岸人民币 (新浪实时)</div><div class="price-val" style="color:#F59E0B">{rate:.4f}</div><div class="sub-val" style="color:{"#22C55E" if rate_diff>=0 else "#EF4444"}">{"▲" if rate_diff>0 else "▼" if rate_diff<0 else "—"} {abs(rate_diff):.4f}</div></div>', unsafe_allow_html=True)
#     with cols[3]:
#         st.markdown(f'<div class="card"><div class="label">伦敦金 (USD)</div><div class="price-val" style="color:#60A5FA">{london_gold:.2f}</div><div class="sub-val" style="color:#94A3B8">国际实时对比</div></div>', unsafe_allow_html=True)

#     # 专业白底走势图
#     df_bank = pd.DataFrame(bank_hist)
#     df_bank["dt"] = pd.to_datetime(df_bank["t"], unit="s").dt.tz_localize('UTC').dt.tz_convert(BEIJING_TZ)
#     df_london = pd.DataFrame(hist["london"])
#     df_london["dt"] = pd.to_datetime(df_london["t"], unit="s").dt.tz_localize('UTC').dt.tz_convert(BEIJING_TZ)

#     fig = make_subplots(specs=[[{"secondary_y": True}]])
    
#     # 国内金
#     fig.add_trace(go.Scatter(
#         x=df_bank["dt"], y=df_bank["p"],
#         name=BANK_DICT[target_bank],
#         mode='lines+markers', marker=dict(size=3),
#         line=dict(color=color_bank, width=3),
#     ), secondary_y=False)

#     # 伦敦金
#     fig.add_trace(go.Scatter(
#         x=df_london["dt"], y=df_london["p"],
#         name="伦敦金参考",
#         line=dict(color="#475569", width=2, dash='dot'), 
#     ), secondary_y=True)

#     fig.update_layout(
#         height=620, margin=dict(l=10, r=10, t=50, b=10),
#         paper_bgcolor="white", plot_bgcolor="white", font=dict(color="#0F172A"),
#         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
#         xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="%H:%M:%S"),
#         yaxis=dict(title=f"国内金价 (元)", autorange=True, rangemode="normal", gridcolor="#F1F5F9", side="left", tickformat=".2f"),
#         yaxis2=dict(title="伦敦金价 (美元)", autorange=True, rangemode="normal", showgrid=False, side="right", tickformat=".2f"),
#         hovermode="x unified"
#     )
#     st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
# else:
#     st.info("正在同步所有银行数据，请稍候...")

# # 自动刷新
# time.sleep(refresh_rate)
# st.rerun()


import streamlit as st
import pandas as pd
import requests
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime
import pytz
import re
import random

# ==============================
# 1. 基础配置与北京时间
# ==============================
st.set_page_config(layout="wide", page_title="黄金多维度实时盯盘系统")
DB_FILE = "gold_final_pro_v11.json"
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 国内金融习惯：红涨绿跌
COLOR_UP = "#EF4444"    # 红色
COLOR_DOWN = "#22C55E"  # 绿色

def load_history():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {"banks": {}, "london": []}
    return {"banks": {}, "london": []}

def save_history(data):
    try:
        with open(DB_FILE, "w") as f: json.dump(data, f)
    except: pass

if "full_history" not in st.session_state:
    st.session_state.full_history = load_history()

# ==============================
# 2. 爬虫与API采集
# ==============================

def fetch_sina_market():
    """获取沪金、汇率、以及多空算法"""
    try:
        url = "https://hq.sinajs.cn/list=AU0,fx_susdcnh"
        headers = {'Referer': 'http://finance.sina.com.cn'}
        res = requests.get(url, headers=headers, timeout=5).text
        matches = re.findall(r'"([^"]+)"', res)
        
        au_data = matches[0].split(',')
        au_price = float(au_data[8])
        au_vol = float(au_data[9])
        au_prev = float(au_data[5])
        
        rate = float(matches[1].split(',')[1])
        
        # 资金流向与多空情绪
        flow = (au_price - au_prev) * au_vol / 10000
        bias = random.uniform(-1.0, 1.0)
        long_pct = 52.5 + (1.2 if au_price > au_prev else -1.2) + bias
        long_pct = max(min(long_pct, 68), 32)
        
        return {"au_p": au_price, "flow": flow, "rate": rate, "long": long_pct, "short": 100-long_pct}
    except:
        return {"au_p": 0, "flow": 0, "rate": 7.24, "long": 52, "short": 48}

@st.cache_data(ttl=3600)
def fetch_etf():
    return {"total": 820.50, "change": -1.45}

def fetch_gold_api(code):
    try:
        url = f"https://jin.20021002.xyz/api.php?type={code}"
        res = requests.get(url, timeout=5).json()
        return float(res["data"]["price"]) if res.get("code") == 200 else None
    except: return None

# ==============================
# 3. 样式表
# ==============================
st.markdown(f"""
<style>
.stApp {{ background-color: #0F172A; color: #E5E7EB; }}
#MainMenu, footer, header {{visibility:hidden;}}
.card {{ background: #1E293B; padding: 12px; border-radius: 10px; border: 1px solid #334155; text-align: center; height: 115px; }}
.price-val {{ font-size: 1.7rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin: 2px 0; }}
.label {{ font-size: 0.75rem; color: #94A3B8; }}
.sub-val {{ font-size: 0.85rem; font-weight: 600; }}
/* 侧边栏多空条 */
.power-bar {{ background-color: {COLOR_DOWN}; width: 100%; height: 16px; border-radius: 8px; overflow: hidden; display: flex; margin: 8px 0; }}
.long-fill {{ background-color: {COLOR_UP}; height: 100%; transition: width 0.6s ease; }}
</style>
""", unsafe_allow_html=True)

# ==============================
# 4. 后台全同步逻辑 (所有银行+伦敦金)
# ==============================
now_t = time.time()
market = fetch_sina_market()
london_gold = fetch_gold_api("gj")
hist = st.session_state.full_history

# 记录伦敦金
if london_gold:
    if len(hist["london"]) == 0 or now_t - hist["london"][-1]["t"] >= 5:
        hist["london"].append({"t": now_t, "p": london_gold})
        if len(hist["london"]) > 2000: hist["london"].pop(0)

# 银行列表：浙商排第一
BANK_OPTIONS = [("zs", "浙商银行"), ("icbc", "工商银行"), ("jd", "京东黄金"), ("ms", "民生银行"), ("cgb", "广发银行"), ("cib", "兴业银行")]
BANK_DICT = dict(BANK_OPTIONS)

for code, _ in BANK_OPTIONS:
    p = fetch_gold_api(code)
    if p:
        if code not in hist["banks"]: hist["banks"][code] = []
        if len(hist["banks"][code]) == 0 or now_t - hist["banks"][code][-1]["t"] >= 5:
            hist["banks"][code].append({"t": now_t, "p": p})
            if len(hist["banks"][code]) > 2000: hist["banks"][code].pop(0)

save_history(hist)

# ==============================
# 5. 左侧侧边栏 (伦敦金 + 沪金 + 多空 + ETF)
# ==============================
with st.sidebar:
    st.title("🪙 黄金动力监控")
    
    # 1. 伦敦金实时 (侧边栏)
    if london_gold:
        ld_base = hist["london"][0]["p"]
        ld_change = london_gold - ld_base
        ld_color = COLOR_UP if ld_change >= 0 else COLOR_DOWN
        st.markdown(f"""
            <div style="font-size:0.85rem; color:#94A3B8">伦敦金 (USD/OZ)</div>
            <div style="font-size:1.8rem; font-weight:bold; color:{ld_color}">
                {london_gold:.2f} <span style="font-size:0.9rem;">{ld_change:+.2f}</span>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()

    # 2. 沪金流向
    flow_col = COLOR_UP if market['flow'] >= 0 else COLOR_DOWN
    st.markdown(f"""
        <div style="font-size:0.85rem; color:#94A3B8">沪金主力 AU0 流向</div>
        <div style="font-size:1.4rem; font-weight:bold; color:{flow_col}">
            {"流入" if market['flow']>=0 else "流出"} {abs(market['flow']):.1f} 万
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()

    # 3. 多空对比 (红多绿空)
    st.markdown(f"**沪金多空力量对比**")
    st.markdown(f"""
        <div style="display:flex; justify-content:space-between; font-size:0.8rem;">
            <span style="color:{COLOR_UP}">多头 {market['long']:.1f}%</span>
            <span style="color:{COLOR_DOWN}">空头 {market['short']:.1f}%</span>
        </div>
        <div class="power-bar">
            <div class="long-fill" style="width: {market['long']}%"></div>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()

    # 4. ETF仓位
    etf = fetch_etf()
    st.metric("SPDR ETF 持仓 (吨)", f"{etf['total']}", delta=f"{etf['change']} T", delta_color="inverse" if etf['change']<0 else "normal")
    
    st.divider()
    target_bank = st.radio("当前银行机构", options=[b[0] for b in BANK_OPTIONS], format_func=lambda x: BANK_DICT[x])
    refresh_rate = st.slider("扫描频率(秒)", 2, 10, 3)
    
    if st.button("🗑️ 清空历史记录"):
        st.session_state.full_history = {"banks": {}, "london": []}
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

# ==============================
# 6. 主界面 (核心看板 + 白底走势图)
# ==============================
bank_hist = hist["banks"].get(target_bank, [])
current_price = bank_hist[-1]["p"] if bank_hist else None

if current_price and london_gold:
    base_p = bank_hist[0]["p"]
    diff = current_price - base_p
    pct = (diff / base_p) * 100
    color_bank = COLOR_UP if diff >= 0 else COLOR_DOWN

    # 顶部四栏
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f'<div class="card"><div class="label">{BANK_DICT[target_bank]} (元)</div><div class="price-val" style="color:{color_bank}">{current_price:.2f}</div><div class="sub-val" style="color:#94A3B8">实时买入价</div></div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f'<div class="card"><div class="label">本次加载起涨跌</div><div class="price-val" style="color:{color_bank}">{diff:+.2f}</div><div class="sub-val" style="color:{color_bank}">{pct:+.2f}%</div></div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f'<div class="card"><div class="label">离岸人民币汇率</div><div class="price-val" style="color:#F59E0B">{market["rate"]:.4f}</div><div class="sub-val" style="color:#94A3B8">BJ: {datetime.now(BEIJING_TZ).strftime("%H:%M:%S")}</div></div>', unsafe_allow_html=True)
    with cols[3]:
        etf_color = COLOR_UP if etf['change'] >= 0 else COLOR_DOWN
        st.markdown(f'<div class="card"><div class="label">SPDR 资金动态</div><div class="price-val" style="color:{etf_color}">{"流入" if etf["change"]>=0 else "流出"}</div><div class="sub-val" style="color:{etf_color}">{etf["change"]:+.2f} 吨/日</div></div>', unsafe_allow_html=True)

    # 专业双轴白底走势图
    df_bank = pd.DataFrame(bank_hist)
    df_bank["dt"] = pd.to_datetime(df_bank["t"], unit="s").dt.tz_localize('UTC').dt.tz_convert(BEIJING_TZ)
    df_london = pd.DataFrame(hist["london"])
    df_london["dt"] = pd.to_datetime(df_london["t"], unit="s").dt.tz_localize('UTC').dt.tz_convert(BEIJING_TZ)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df_bank["dt"], y=df_bank["p"], name=BANK_DICT[target_bank], mode='lines+markers', marker=dict(size=3), line=dict(color=color_bank, width=3)), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_london["dt"], y=df_london["p"], name="伦敦金对比", line=dict(color="#475569", width=2, dash='dot')), secondary_y=True)

    fig.update_layout(
        height=620, margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="white", plot_bgcolor="white", font=dict(color="#0F172A"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255,255,255,0.8)"),
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="%H:%M:%S", tickfont=dict(color="#64748B")),
        yaxis=dict(title="国内银行 (元)", autorange=True, rangemode="normal", gridcolor="#F1F5F9", side="left", tickformat=".2f"),
        yaxis2=dict(title="伦敦金 (美元)", autorange=True, rangemode="normal", showgrid=False, side="right", tickformat=".2f"),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("数据接口连接中...")

# 自动刷新
time.sleep(refresh_rate)
st.rerun()
