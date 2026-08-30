import json
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="TJ AmeriTrade", page_icon="📈", layout="wide")

CSS = r"""
<style>
:root{--bg:#07111f;--panel:#0d1b2d;--panel2:#10233b;--border:rgba(120,169,255,.18);--text:#eef4ff;--muted:#a9bddb;--blue:#4f8cff;--green:#39d98a;--red:#ff6b6b;--amber:#ffb85c;--purple:#9d7dff}
.stApp{background:radial-gradient(circle at top left,rgba(41,102,255,.14),transparent 26%),linear-gradient(180deg,#07111f 0%,#081526 100%);color:var(--text)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#050d18,#07111f);border-right:1px solid rgba(255,255,255,.06)}
.block-container{padding-top:1.8rem!important;padding-bottom:2.2rem!important;max-width:1480px}
[data-testid="stVerticalBlock"]{gap:.85rem}
[data-testid="column"]>[data-testid="stVerticalBlock"]{gap:.55rem}
h1,h2,h3,h4,h5,h6,p,label,div,span{color:var(--text)}
.page-title{font-size:2.35rem;font-weight:800;letter-spacing:-.035em;line-height:1.05;margin:0 0 .35rem}
.kicker{color:#9fb7da;font-size:.86rem;letter-spacing:.1em;text-transform:uppercase;margin-bottom:1.15rem}
.hero,.metric-card,.panel{background:linear-gradient(180deg,rgba(16,35,59,.92),rgba(10,23,39,.96));border:1px solid var(--border);box-shadow:0 12px 30px rgba(0,0,0,.16)}
.hero{border-radius:22px;padding:1.25rem 1.35rem;margin:.15rem 0 .15rem}
.metric-card{border-radius:18px;padding:1rem 1rem .9rem;min-height:122px}
.panel{border-radius:20px;padding:1.2rem 1.25rem}
.metric-label{color:var(--muted);font-size:.9rem;margin-bottom:.42rem}.metric-value{font-size:1.8rem;font-weight:800;letter-spacing:-.03em;line-height:1.1}.metric-sub{color:var(--muted);font-size:.84rem;margin-top:.34rem}
.section-title{font-size:1.2rem;font-weight:800;margin-bottom:.2rem}.section-sub{color:var(--muted);font-size:.88rem;margin-bottom:.85rem}
.badge{display:inline-block;padding:.3rem .62rem;border-radius:999px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);font-size:.79rem;margin-left:.35rem}
.score-row{display:grid;grid-template-columns:150px 1fr 64px;gap:12px;align-items:center;margin:.78rem 0}.track{height:12px;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden}.fill{height:100%;border-radius:999px}
.rating-wrap{display:flex;gap:1.15rem;align-items:center;flex-wrap:wrap}.ring{width:166px;height:166px;border-radius:999px;display:flex;align-items:center;justify-content:center;padding:11px}.ring-inner{width:100%;height:100%;border-radius:999px;background:#0b1627;display:flex;flex-direction:column;align-items:center;justify-content:center;border:1px solid rgba(255,255,255,.05)}.ring-num{font-size:2.8rem;font-weight:800;line-height:1}.ring-call{font-weight:800;color:#69b0ff;margin-top:.25rem}
.note{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:.8rem .95rem;color:var(--muted);font-size:.86rem}.small{color:var(--muted);font-size:.84rem}
.stButton>button{min-height:42px;border-radius:12px;border:1px solid rgba(98,145,255,.28);background:linear-gradient(180deg,#3976ff,#2c63e7);color:white;font-weight:700}
.stTextInput input,.stSelectbox div[data-baseweb="select"]>div,.stMultiSelect div[data-baseweb="select"]>div{min-height:42px;background:rgba(10,20,36,.92);border:1px solid rgba(111,149,214,.26);border-radius:12px;color:var(--text)}
[data-testid="stSidebar"] .stButton>button{width:100%}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.55rem}
@media(max-width:900px){.score-row{grid-template-columns:120px 1fr 58px}.block-container{padding-top:1rem!important}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

HEADERS={"User-Agent":"Mozilla/5.0"}
TIMEFRAMES={"1M":"1mo","3M":"3mo","6M":"6mo","YTD":"ytd","1Y":"1y","3Y":"3y","5Y":"5y"}
UNIVERSE={
    "META":"Meta Platforms, Inc.","GOOGL":"Alphabet Inc.","GOOG":"Alphabet Inc. Class C","AMZN":"Amazon.com, Inc.",
    "NVDA":"NVIDIA Corporation","MSFT":"Microsoft Corporation","AAPL":"Apple Inc.","TSM":"Taiwan Semiconductor","MU":"Micron Technology, Inc.",
    "SOFI":"SoFi Technologies, Inc.","CELH":"Celsius Holdings, Inc.","IREN":"IREN Limited","PYPL":"PayPal Holdings, Inc.","SPY":"SPDR S&P 500 ETF Trust","QQQ":"Invesco QQQ Trust"
}
if "watchlist" not in st.session_state: st.session_state.watchlist=["META","GOOGL","NVDA","MU"]
if "active_symbol" not in st.session_state: st.session_state.active_symbol="META"

@st.cache_data(ttl=120,show_spinner=False)
def yahoo_quote(symbol):
    url="https://query1.finance.yahoo.com/v7/finance/quote"
    try:
        r=requests.get(url,params={"symbols":symbol},headers=HEADERS,timeout=8)
        r.raise_for_status()
        rows=r.json().get("quoteResponse",{}).get("result",[])
        return rows[0] if rows else {}
    except Exception:
        return {}

@st.cache_data(ttl=600,show_spinner=False)
def yahoo_search(q):
    if not q or len(q)<1:return []
    try:
        r=requests.get("https://query2.finance.yahoo.com/v1/finance/search",params={"q":q,"quotesCount":8,"newsCount":0},headers=HEADERS,timeout=8)
        r.raise_for_status()
        out=[]
        for x in r.json().get("quotes",[]):
            sym=x.get("symbol"); name=x.get("shortname") or x.get("longname") or sym; exch=x.get("exchange") or ""
            if sym and x.get("quoteType") in {"EQUITY","ETF"}: out.append((sym,name,exch))
        return out[:8]
    except Exception:return []

@st.cache_data(ttl=900,show_spinner=False)
def history(symbol,period="1y"):
    try:
        d=yf.download(symbol,period=period,progress=False,auto_adjust=False,threads=False)
        if d is None or d.empty:return pd.DataFrame()
        if isinstance(d.columns,pd.MultiIndex): d.columns=d.columns.get_level_values(0)
        d=d.reset_index()
        return d
    except Exception:return pd.DataFrame()

@st.cache_data(ttl=1800,show_spinner=False)
def info_fallback(symbol):
    try:return yf.Ticker(symbol).get_info() or {}
    except Exception:
        try:return yf.Ticker(symbol).info or {}
        except Exception:return {}

def safe(v):
    try:return float(v)
    except Exception:return np.nan

def fmt_money(v):
    if pd.isna(v):return "—"
    s="-" if v<0 else ""; a=abs(v)
    if a>=1e12:return f"{s}${a/1e12:.2f}T"
    if a>=1e9:return f"{s}${a/1e9:.2f}B"
    if a>=1e6:return f"{s}${a/1e6:.2f}M"
    return f"{s}${a:,.2f}"

def fmt_pct(v): return "—" if pd.isna(v) else f"{v*100:.1f}%"

def one_year_return(h):
    if h.empty:return np.nan
    c=h["Close"].dropna()
    if len(c)<2:return np.nan
    start=c.iloc[-252] if len(c)>252 else c.iloc[0]
    return c.iloc[-1]/start-1 if start else np.nan

def merged_data(symbol):
    q=yahoo_quote(symbol); info=info_fallback(symbol)
    h=history(symbol,"5y")
    def first(*keys):
        for k in keys:
            v=q.get(k)
            if v not in (None,""):return v
            v=info.get(k)
            if v not in (None,""):return v
        return None
    price=safe(first("regularMarketPrice","currentPrice"))
    if pd.isna(price) and not h.empty: price=safe(h["Close"].dropna().iloc[-1])
    return {
        "quote":q,"info":info,"history":h,"price":price,
        "company":first("longName","shortName") or UNIVERSE.get(symbol,symbol),
        "sector":first("sector") or "—","industry":first("industry") or "—","exchange":first("fullExchangeName","exchange") or "—",
        "market_cap":safe(first("marketCap")),"forward_pe":safe(first("forwardPE")),"trailing_pe":safe(first("trailingPE")),
        "revenue_growth":safe(first("revenueGrowth")),"earnings_growth":safe(first("earningsGrowth")),
        "total_cash":safe(first("totalCash")),"total_debt":safe(first("totalDebt")),"op_margin":safe(first("operatingMargins")),
        "roe":safe(first("returnOnEquity")),"de":safe(first("debtToEquity"))
    }

def clamp(x):return max(0,min(10,float(x)))

def calc_scores(d):
    h=d["history"]; pe=d["forward_pe"] if not pd.isna(d["forward_pe"]) else d["trailing_pe"]; rg=d["revenue_growth"]; eg=d["earnings_growth"]; margin=d["op_margin"]; roe=d["roe"]; de=d["de"]; ret=one_year_return(h)
    valuation=6.0 if pd.isna(pe) else clamp(10-max(pe-12,0)*.16)
    quality=float(np.mean([5 if pd.isna(margin) else clamp(5+margin*14),5 if pd.isna(roe) else clamp(5+roe*10),6 if pd.isna(de) else clamp(9-de/55)]))
    growth=float(np.mean([5 if pd.isna(rg) else clamp(5+rg*15),5 if pd.isna(eg) else clamp(5+eg*12)]))
    momentum=5.0
    if not h.empty and len(h)>=50:
        c=h["Close"].dropna(); p=c.iloc[-1]; ma50=c.rolling(50).mean().iloc[-1]; ma200=c.rolling(200).mean().iloc[-1] if len(c)>=200 else np.nan
        momentum=5+(1.5 if p>ma50 else -1)+(1.5 if not pd.isna(ma200) and p>ma200 else 0)+(1 if not pd.isna(ret) and ret>.15 else (-1 if not pd.isna(ret) and ret<0 else 0)); momentum=clamp(momentum)
    total=round(float(np.average([valuation,quality,growth,momentum],weights=[.3,.25,.25,.2])),1)
    call="STRONG BUY" if total>=8.5 else "BUY" if total>=7 else "HOLD" if total>=5 else "REDUCE" if total>=3.5 else "AVOID"
    return {"Valuation":round(valuation,1),"Financial Quality":round(quality,1),"Growth":round(growth,1),"Momentum":round(momentum,1),"TJ Rating":total,"Call":call}

def metric_card(label,value,sub,color="#eef4ff"):
    return f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value' style='color:{color}'>{value}</div><div class='metric-sub'>{sub}</div></div>"

def rating_panel(s):
    pct=s['TJ Rating']*10
    return f"<div class='panel'><div class='section-title'>TJ Rating</div><div class='section-sub'>Composite research score across valuation, quality, growth and momentum.</div><div class='rating-wrap'><div class='ring' style='background:conic-gradient(#4f8cff {pct}%,rgba(255,255,255,.08) 0)'><div class='ring-inner'><div class='ring-num'>{s['TJ Rating']:.1f}</div><div class='ring-call'>{s['Call']}</div></div></div><div class='note'><b>How to read it</b><br>Higher scores indicate a stronger overall setup. Use this as a research signal, not investment advice.</div></div></div>"

def score_panel(s):
    colors={"Valuation":"#4f8cff","Financial Quality":"#9d7dff","Growth":"#39d98a","Momentum":"#ffb85c"}; rows=""
    for k in colors:
        v=s[k]; rows+=f"<div class='score-row'><div>{k}</div><div class='track'><div class='fill' style='width:{v*10}%;background:{colors[k]}'></div></div><div style='text-align:right;font-weight:700'>{v:.1f}/10</div></div>"
    return f"<div class='panel'><div class='section-title'>Category Scores</div><div class='section-sub'>Quickly understand where the stock is strong and where it is weak.</div>{rows}</div>"

def perf_chart(symbol,period):
    fig=go.Figure()
    for name in [symbol,"SPY"]:
        d=history(name,period)
        if d.empty:continue
        c=d["Close"].dropna(); base=c.iloc[0]; fig.add_trace(go.Scatter(x=d.loc[c.index,"Date"],y=c/base*100,mode="lines",name=name,line={"width":3}))
    fig.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=350,margin=dict(l=10,r=10,t=20,b=5),legend=dict(orientation="h",y=1.02,x=0))
    fig.update_xaxes(gridcolor="rgba(255,255,255,.06)");fig.update_yaxes(gridcolor="rgba(255,255,255,.06)")
    return fig

st.sidebar.markdown("<div style='font-size:1.85rem;font-weight:800;margin-top:.35rem'>📈 TJ AmeriTrade</div>",unsafe_allow_html=True)
st.sidebar.markdown("<div class='small' style='margin-bottom:.8rem'>Market research made easier to read.</div>",unsafe_allow_html=True)
page=st.sidebar.radio("Navigation",["Analyzer","Watchlist","Top TJ Buys","Performance Compare"],label_visibility="collapsed")
st.sidebar.markdown("---")
add=st.sidebar.text_input("Add ticker",placeholder="e.g. AAPL").upper().strip()
if st.sidebar.button("+ Add to Watchlist",use_container_width=True) and add and add not in st.session_state.watchlist: st.session_state.watchlist.append(add)
st.sidebar.markdown("<div class='note'>TJ Rating is a research signal, not investment advice.</div>",unsafe_allow_html=True)

if page=="Analyzer":
    st.markdown("<div class='page-title'>Analyzer</div>",unsafe_allow_html=True)
    st.markdown("<div class='kicker'>Market Intelligence • Valuation • Growth • Momentum • Relative Strength</div>",unsafe_allow_html=True)

    q=st.text_input("Search stock or ticker",value=st.session_state.active_symbol,placeholder="Type META, Apple, NVIDIA…")
    suggestions=yahoo_search(q)
    if not suggestions and q.upper() in UNIVERSE:suggestions=[(q.upper(),UNIVERSE[q.upper()],"")]
    options=[f"{sym} — {name}" for sym,name,_ in suggestions]
    if options:
        picked=st.selectbox("Matching securities",options,index=0,label_visibility="collapsed")
        selected_symbol=picked.split(" — ",1)[0].strip().upper()
    else:selected_symbol=q.upper().strip() or st.session_state.active_symbol
    csearch1,csearch2=st.columns([5,1.1])
    with csearch1: st.caption(f"Selected: {selected_symbol} • data refreshes automatically")
    with csearch2:
        if st.button("Analyze",use_container_width=True): st.session_state.active_symbol=selected_symbol; st.cache_data.clear(); st.rerun()
    symbol=st.session_state.active_symbol

    with st.spinner(f"Syncing {symbol}…"): d=merged_data(symbol)
    h=d['history']; qd=d['quote']; info=d['info']
    if h.empty and not qd and not info: st.error(f"Could not load data for {symbol}. Try again in a moment."); st.stop()

    cap="Large Cap" if not pd.isna(d['market_cap']) and d['market_cap']>=10e9 else "Mid/Small Cap"
    st.markdown(f"<div class='hero'><div style='display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;align-items:flex-start'><div><div style='font-size:2rem;font-weight:800'>{symbol}</div><div style='font-size:1.45rem;color:#d7e6ff;margin-top:.1rem'>{d['company']}</div><div class='small' style='margin-top:.45rem'>{d['sector']} • {d['industry']}</div></div><div><span class='badge'>{d['exchange']}</span><span class='badge'>{cap}</span></div></div></div>",unsafe_allow_html=True)

    net=np.nan if pd.isna(d['total_cash']) and pd.isna(d['total_debt']) else (0 if pd.isna(d['total_cash']) else d['total_cash'])-(0 if pd.isna(d['total_debt']) else d['total_debt'])
    r1=one_year_return(h); pe=d['forward_pe'] if not pd.isna(d['forward_pe']) else d['trailing_pe']; pe_label="Forward P/E" if not pd.isna(d['forward_pe']) else "P/E"
    vals=[("Price",fmt_money(d['price']),"Latest market price","#eef4ff"),(pe_label,f"{pe:.1f}x" if not pd.isna(pe) else "—","Current valuation multiple","#69b0ff"),("Net Cash",fmt_money(net),"Cash minus debt","#39d98a" if not pd.isna(net) and net>=0 else "#ff6b6b"),("Revenue Growth",fmt_pct(d['revenue_growth']),"Year-over-year","#39d98a" if not pd.isna(d['revenue_growth']) and d['revenue_growth']>=0 else "#ff6b6b"),("1Y Return",fmt_pct(r1),"Trailing 12 months","#39d98a" if not pd.isna(r1) and r1>=0 else "#ff6b6b")]
    cols=st.columns(5,gap="small")
    for col,v in zip(cols,vals):
        with col: st.markdown(metric_card(*v),unsafe_allow_html=True)

    s=calc_scores(d); a,b=st.columns([1.05,1.7],gap="small")
    with a: st.markdown(rating_panel(s),unsafe_allow_html=True)
    with b: st.markdown(score_panel(s),unsafe_allow_html=True)

    st.markdown("<div class='panel'><div class='section-title'>Performance vs SPY</div><div class='section-sub'>Indexed performance makes relative strength easier to compare.</div>",unsafe_allow_html=True)
    tf=st.radio("Timeframe",list(TIMEFRAMES),horizontal=True,index=4)
    st.plotly_chart(perf_chart(symbol,TIMEFRAMES[tf]),use_container_width=True)
    st.markdown("</div>",unsafe_allow_html=True)

elif page=="Watchlist":
    st.markdown("<div class='page-title'>Watchlist</div><div class='kicker'>Your tracked names, simplified</div>",unsafe_allow_html=True)
    rows=[]
    for sym in st.session_state.watchlist:
        d=merged_data(sym); s=calc_scores(d); rows.append({"Ticker":sym,"Company":d['company'],"Price":None if pd.isna(d['price']) else round(d['price'],2),"1Y Return %":None if pd.isna(one_year_return(d['history'])) else round(one_year_return(d['history'])*100,1),"TJ Rating":s['TJ Rating'],"Call":s['Call']})
    st.dataframe(pd.DataFrame(rows).sort_values("TJ Rating",ascending=False),use_container_width=True,hide_index=True)

elif page=="Top TJ Buys":
    st.markdown("<div class='page-title'>Top TJ Buys</div><div class='kicker'>Ranked research screen</div>",unsafe_allow_html=True)
    rows=[]
    for sym in list(dict.fromkeys(list(UNIVERSE)[:12]+st.session_state.watchlist)):
        d=merged_data(sym); s=calc_scores(d); rows.append({"Ticker":sym,"Company":d['company'],"Price":None if pd.isna(d['price']) else round(d['price'],2),"TJ Rating":s['TJ Rating'],"Valuation":s['Valuation'],"Quality":s['Financial Quality'],"Growth":s['Growth'],"Momentum":s['Momentum'],"Call":s['Call']})
    st.dataframe(pd.DataFrame(rows).sort_values("TJ Rating",ascending=False),use_container_width=True,hide_index=True)

else:
    st.markdown("<div class='page-title'>Performance Compare</div><div class='kicker'>Compare multiple names with less clutter</div>",unsafe_allow_html=True)
    picks=st.multiselect("Tickers",options=list(UNIVERSE),default=["META","GOOGL","NVDA","SPY"])
    tf=st.radio("Timeframe",list(TIMEFRAMES),horizontal=True,index=3,key="cmp_tf")
    fig=go.Figure()
    for sym in picks:
        d=history(sym,TIMEFRAMES[tf])
        if d.empty:continue
        c=d['Close'].dropna(); base=c.iloc[0]; fig.add_trace(go.Scatter(x=d.loc[c.index,'Date'],y=c/base*100,mode='lines',name=sym,line={'width':3}))
    fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',height=470,margin=dict(l=10,r=10,t=20,b=10),legend=dict(orientation='h',y=1.02,x=0))
    fig.update_xaxes(gridcolor='rgba(255,255,255,.06)');fig.update_yaxes(gridcolor='rgba(255,255,255,.06)')
    st.plotly_chart(fig,use_container_width=True)
