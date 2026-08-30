import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="TJ AmeriTrade", page_icon="📈", layout="wide")

st.markdown("""
<style>
:root {
  --bg:#07111f; --panel:#0d1b2d; --panel2:#10233b; --border:rgba(120,169,255,.18);
  --text:#eef4ff; --muted:#a9bddb; --accent:#4f8cff; --blue2:#69b0ff;
  --green:#39d98a; --red:#ff6b6b; --amber:#ffb85c; --purple:#9d7dff;
}
.stApp {
  background:radial-gradient(circle at top left,rgba(41,102,255,.17),transparent 25%),
             linear-gradient(180deg,#07111f 0%,#081526 100%);
  color:var(--text);
}
[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#050d18 0%,#07111f 100%);
  border-right:1px solid rgba(255,255,255,.06);
}
.block-container {padding-top:1.2rem; max-width:1500px;}
h1,h2,h3,h4,h5,h6,p,label,div,span {color:var(--text);}
.title {font-size:2.2rem;font-weight:800;letter-spacing:-.03em;margin-bottom:.2rem;}
.sub {color:var(--muted);font-size:.88rem;letter-spacing:.08em;text-transform:uppercase;margin-bottom:1.1rem;}
.hero,.card,.panel {
  background:linear-gradient(180deg,rgba(16,35,59,.90),rgba(10,23,39,.94));
  border:1px solid var(--border); border-radius:20px; box-shadow:0 12px 32px rgba(0,0,0,.18);
}
.hero {padding:1.25rem 1.35rem;margin-bottom:1rem;}
.card {padding:1rem;min-height:126px;}
.panel {padding:1.15rem 1.25rem;}
.metric-label {color:var(--muted);font-size:.93rem;margin-bottom:.45rem;}
.metric {font-size:1.85rem;font-weight:800;letter-spacing:-.03em;line-height:1.1;}
.metric-sub {color:var(--muted);font-size:.86rem;margin-top:.35rem;}
.badge {display:inline-block;padding:.3rem .65rem;border-radius:999px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);font-size:.8rem;margin-left:.35rem;}
.section-title {font-size:1.25rem;font-weight:800;margin-bottom:.2rem;}
.section-sub {color:var(--muted);font-size:.9rem;margin-bottom:.8rem;}
.score-row {display:grid;grid-template-columns:150px 1fr 65px;gap:12px;align-items:center;margin:.8rem 0;}
.track {height:13px;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden;}
.fill {height:100%;border-radius:999px;}
.rating-wrap {display:flex;gap:1.2rem;align-items:center;flex-wrap:wrap;}
.ring {width:170px;height:170px;border-radius:999px;display:flex;align-items:center;justify-content:center;padding:11px;}
.ring-inner {width:100%;height:100%;border-radius:999px;background:#0b1627;display:flex;flex-direction:column;align-items:center;justify-content:center;border:1px solid rgba(255,255,255,.05);}
.ring-num {font-size:3rem;font-weight:800;line-height:1;}
.ring-call {font-weight:800;color:var(--blue2);margin-top:.25rem;}
.note {background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:.8rem 1rem;color:var(--muted);font-size:.88rem;}
.small {color:var(--muted);font-size:.86rem;}
.stButton>button {border-radius:12px;border:1px solid rgba(98,145,255,.28);background:linear-gradient(180deg,#3371ff,#2562eb);color:#fff;font-weight:700;}
.stTextInput input,.stSelectbox div[data-baseweb="select"]>div,.stMultiSelect div[data-baseweb="select"]>div {background:rgba(10,20,36,.88);border:1px solid rgba(111,149,214,.22);border-radius:12px;color:var(--text);}
</style>
""", unsafe_allow_html=True)

if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["META", "GOOGL", "NVDA", "MU"]

TIMEFRAMES = {"1M":"1mo","3M":"3mo","6M":"6mo","YTD":"ytd","1Y":"1y","3Y":"3y","5Y":"5y"}
UNIVERSE = ["META","GOOGL","AMZN","NVDA","MSFT","AAPL","TSM","MU","SOFI","CELH","IREN","PYPL"]

@st.cache_data(ttl=900, show_spinner=False)
def hist(symbol, period="1y"):
    df = yf.Ticker(symbol).history(period=period, auto_adjust=False)
    if df is None or df.empty:
        return pd.DataFrame()
    return df.reset_index()

@st.cache_data(ttl=900, show_spinner=False)
def quote(symbol):
    t = yf.Ticker(symbol)
    try: info = t.info or {}
    except Exception: info = {}
    try: fast = dict(t.fast_info)
    except Exception: fast = {}
    return info, fast, hist(symbol,"5y")

def safe(v):
    try: return float(v)
    except Exception: return np.nan

def price_of(info, fast, h):
    for k in ["lastPrice","regularMarketPrice","currentPrice"]:
        v = fast.get(k, info.get(k))
        if v is not None:
            try: return float(v)
            except Exception: pass
    return float(h["Close"].iloc[-1]) if not h.empty else np.nan

def fmt_money(v):
    if pd.isna(v): return "—"
    s = "-" if v < 0 else ""; a = abs(v)
    if a >= 1e12: return f"{s}${a/1e12:.2f}T"
    if a >= 1e9: return f"{s}${a/1e9:.2f}B"
    if a >= 1e6: return f"{s}${a/1e6:.2f}M"
    return f"{s}${a:,.2f}"

def fmt_pct(v):
    return "—" if pd.isna(v) else f"{v*100:.1f}%"

def one_year_return(h):
    if h.empty: return np.nan
    start = h["Close"].iloc[-252] if len(h) > 252 else h["Close"].iloc[0]
    end = h["Close"].iloc[-1]
    return end/start - 1 if start else np.nan

def clamp(x): return max(0,min(10,float(x)))

def scores(info,h):
    pe = safe(info.get("forwardPE")); rg = safe(info.get("revenueGrowth")); eg = safe(info.get("earningsGrowth"))
    margin = safe(info.get("operatingMargins")); roe = safe(info.get("returnOnEquity")); de = safe(info.get("debtToEquity"))
    ret = one_year_return(h)
    valuation = 8.5 if pd.isna(pe) else clamp(10 - max(pe-15,0)*.12)
    quality_parts = [5 if pd.isna(margin) else clamp(5+margin*14), 5 if pd.isna(roe) else clamp(5+roe*10), 7 if pd.isna(de) else clamp(9-de/55)]
    quality = float(np.mean(quality_parts))
    growth_parts = [5 if pd.isna(rg) else clamp(5+rg*15), 5 if pd.isna(eg) else clamp(5+eg*12)]
    growth = float(np.mean(growth_parts))
    momentum = 5.0
    if not h.empty and len(h)>=50:
        c=h["Close"]; p=c.iloc[-1]; ma50=c.rolling(50).mean().iloc[-1]; ma200=c.rolling(200).mean().iloc[-1] if len(c)>=200 else np.nan
        momentum = 5 + (1.5 if p>ma50 else -1) + (1.5 if not pd.isna(ma200) and p>ma200 else 0)
        if not pd.isna(ret): momentum += 1 if ret>0.15 else (-1 if ret<0 else 0)
        momentum=clamp(momentum)
    total=round(float(np.average([valuation,quality,growth,momentum],weights=[.3,.25,.25,.2])),1)
    call="STRONG BUY" if total>=8.5 else "BUY" if total>=7 else "HOLD" if total>=5 else "REDUCE" if total>=3.5 else "AVOID"
    return {"Valuation":round(valuation,1),"Financial Quality":round(quality,1),"Growth":round(growth,1),"Momentum":round(momentum,1),"TJ Rating":total,"Call":call}

def metric_card(label,value,sub,color="#eef4ff"):
    return f"<div class='card'><div class='metric-label'>{label}</div><div class='metric' style='color:{color}'>{value}</div><div class='metric-sub'>{sub}</div></div>"

def score_panel(s):
    colors={"Valuation":"#4f8cff","Financial Quality":"#9d7dff","Growth":"#39d98a","Momentum":"#ffb85c"}
    rows=""
    for k in ["Valuation","Financial Quality","Growth","Momentum"]:
        v=s[k]; rows+=f"<div class='score-row'><div>{k}</div><div class='track'><div class='fill' style='width:{v*10}%;background:{colors[k]}'></div></div><div style='text-align:right;font-weight:700'>{v:.1f}/10</div></div>"
    return f"<div class='panel'><div class='section-title'>Category Scores</div><div class='section-sub'>Quickly understand where the stock is strong and where it is weak.</div>{rows}</div>"

def rating_panel(s):
    pct=s["TJ Rating"]*10
    return f"<div class='panel'><div class='section-title'>TJ Rating</div><div class='section-sub'>Composite research score across valuation, quality, growth and momentum.</div><div class='rating-wrap'><div class='ring' style='background:conic-gradient(#4f8cff {pct}%,rgba(255,255,255,.08) 0)'><div class='ring-inner'><div class='ring-num'>{s['TJ Rating']:.1f}</div><div class='ring-call'>{s['Call']}</div></div></div><div class='note'><b>How to read it</b><br>Higher scores indicate a stronger overall setup. Use this as a research signal, not investment advice.</div></div></div>"

def chart(symbol,period):
    d1=hist(symbol,period); d2=hist("SPY",period); fig=go.Figure()
    for name,d in [(symbol,d1),("SPY",d2)]:
        if d.empty: continue
        base=d["Close"].iloc[0]; y=d["Close"]/base*100
        fig.add_trace(go.Scatter(x=d["Date"],y=y,mode="lines",name=name,line={"width":3}))
    fig.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=360,margin=dict(l=10,r=10,t=20,b=10),legend=dict(orientation="h",y=1.02,x=0))
    fig.update_xaxes(gridcolor="rgba(255,255,255,.06)"); fig.update_yaxes(gridcolor="rgba(255,255,255,.06)")
    return fig

st.sidebar.markdown("<div style='font-size:1.9rem;font-weight:800;margin-top:.3rem'>📈 TJ AmeriTrade</div>",unsafe_allow_html=True)
st.sidebar.markdown("<div class='small' style='margin-bottom:1rem'>Market research made easier to read.</div>",unsafe_allow_html=True)
page=st.sidebar.radio("Navigation",["Analyzer","Watchlist","Top TJ Buys","Performance Compare"],label_visibility="collapsed")
st.sidebar.markdown("---")
add=st.sidebar.text_input("Add ticker",placeholder="Enter ticker (e.g. AAPL)").upper().strip()
if st.sidebar.button("+ Add to Watchlist",use_container_width=True) and add:
    if add not in st.session_state.watchlist: st.session_state.watchlist.append(add)
st.sidebar.markdown("<div class='note'>TJ Rating is a research signal, not investment advice.</div>",unsafe_allow_html=True)

if page=="Analyzer":
    st.markdown("<div class='title'>Analyzer</div>",unsafe_allow_html=True)
    st.markdown("<div class='sub'>Market Intelligence • Valuation • Growth • Momentum • Relative Strength</div>",unsafe_allow_html=True)
    c1,c2=st.columns([5,1.2])
    with c1: symbol=st.text_input("Search ticker",value="META").upper().strip() or "META"
    with c2:
        st.markdown("<div style='height:1.8rem'></div>",unsafe_allow_html=True)
        if st.button("Analyze",use_container_width=True): st.session_state.active_symbol=symbol
    symbol=st.session_state.get("active_symbol",symbol)
    with st.spinner(f"Loading {symbol}…"):
        info,fast,h=quote(symbol)
    if h.empty and not info:
        st.error(f"Could not load {symbol}.")
        st.stop()
    p=price_of(info,fast,h); company=info.get("shortName") or info.get("longName") or symbol
    sector=info.get("sector") or "—"; industry=info.get("industry") or "—"; exchange=info.get("exchange") or "—"
    mc=safe(info.get("marketCap")); cap="Large Cap" if not pd.isna(mc) and mc>=10e9 else "Mid/Small Cap"
    st.markdown(f"<div class='hero'><div style='display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap'><div><div style='font-size:2rem;font-weight:800'>{symbol}</div><div style='font-size:1.45rem;color:#d7e6ff'>{company}</div><div class='small' style='margin-top:.4rem'>{sector} • {industry}</div></div><div><span class='badge'>{exchange}</span><span class='badge'>{cap}</span></div></div></div>",unsafe_allow_html=True)
    pe=safe(info.get("forwardPE")); cash=safe(info.get("totalCash")); debt=safe(info.get("totalDebt")); net=np.nan if pd.isna(cash) and pd.isna(debt) else (0 if pd.isna(cash) else cash)-(0 if pd.isna(debt) else debt)
    rg=safe(info.get("revenueGrowth")); r1=one_year_return(h)
    cols=st.columns(5)
    vals=[("Price",fmt_money(p),"Market Price","#eef4ff"),("Forward P/E",f"{pe:.1f}x" if not pd.isna(pe) else "—","Forward 12M","#69b0ff"),("Net Cash",fmt_money(net),"Cash minus debt","#39d98a" if not pd.isna(net) and net>=0 else "#ff6b6b"),("Revenue Growth",fmt_pct(rg),"YoY Growth","#39d98a" if not pd.isna(rg) and rg>=0 else "#ff6b6b"),("1Y Return",fmt_pct(r1),"Trailing 1 Year","#39d98a" if not pd.isna(r1) and r1>=0 else "#ff6b6b")]
    for col,data in zip(cols,vals):
        with col: st.markdown(metric_card(*data),unsafe_allow_html=True)
    s=scores(info,h)
    a,b=st.columns([1,1.6])
    with a: st.markdown(rating_panel(s),unsafe_allow_html=True)
    with b: st.markdown(score_panel(s),unsafe_allow_html=True)
    st.markdown("<div style='height:1rem'></div>",unsafe_allow_html=True)
    st.markdown("<div class='panel'><div class='section-title'>Performance vs SPY</div><div class='section-sub'>Stock return and excess return relative to the S&P 500 ETF.</div>",unsafe_allow_html=True)
    tf=st.radio("Timeframe",list(TIMEFRAMES.keys()),horizontal=True,index=4)
    st.plotly_chart(chart(symbol,TIMEFRAMES[tf]),use_container_width=True)
    st.markdown("</div>",unsafe_allow_html=True)

elif page=="Watchlist":
    st.markdown("<div class='title'>Watchlist</div>",unsafe_allow_html=True)
    st.markdown("<div class='sub'>Your tracked names, simplified</div>",unsafe_allow_html=True)
    rows=[]
    for sym in st.session_state.watchlist:
        try:
            info,fast,h=quote(sym); s=scores(info,h); p=price_of(info,fast,h)
            rows.append({"Ticker":sym,"Company":info.get("shortName") or sym,"Price":round(p,2) if not pd.isna(p) else None,"TJ Rating":s["TJ Rating"],"Call":s["Call"],"1Y Return %":round(one_year_return(h)*100,1) if not pd.isna(one_year_return(h)) else None})
        except Exception: pass
    st.dataframe(pd.DataFrame(rows).sort_values("TJ Rating",ascending=False) if rows else pd.DataFrame(),use_container_width=True,hide_index=True)

elif page=="Top TJ Buys":
    st.markdown("<div class='title'>Top TJ Buys</div>",unsafe_allow_html=True)
    st.markdown("<div class='sub'>Ranked research screen</div>",unsafe_allow_html=True)
    rows=[]
    for sym in list(dict.fromkeys(UNIVERSE+st.session_state.watchlist)):
        try:
            info,fast,h=quote(sym); s=scores(info,h); p=price_of(info,fast,h)
            rows.append({"Ticker":sym,"Company":info.get("shortName") or sym,"Price":round(p,2) if not pd.isna(p) else None,"TJ Rating":s["TJ Rating"],"Valuation":s["Valuation"],"Quality":s["Financial Quality"],"Growth":s["Growth"],"Momentum":s["Momentum"],"Call":s["Call"]})
        except Exception: pass
    st.dataframe(pd.DataFrame(rows).sort_values("TJ Rating",ascending=False) if rows else pd.DataFrame(),use_container_width=True,hide_index=True)

else:
    st.markdown("<div class='title'>Performance Compare</div>",unsafe_allow_html=True)
    st.markdown("<div class='sub'>Compare multiple names without the clutter</div>",unsafe_allow_html=True)
    picks=st.multiselect("Select tickers",list(dict.fromkeys(UNIVERSE+st.session_state.watchlist+["SPY","QQQ"])),default=["META","SPY"])
    tf=st.radio("Timeframe",list(TIMEFRAMES.keys()),horizontal=True,index=4,key="cmp")
    fig=go.Figure()
    for sym in picks:
        d=hist(sym,TIMEFRAMES[tf])
        if d.empty: continue
        base=d["Close"].iloc[0]; y=d["Close"]/base*100
        fig.add_trace(go.Scatter(x=d["Date"],y=y,mode="lines",name=sym,line={"width":3}))
    fig.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=430,margin=dict(l=10,r=10,t=20,b=10),legend=dict(orientation="h",y=1.02,x=0))
    st.plotly_chart(fig,use_container_width=True)
