from datetime import datetime
import yfinance as yf
import streamlit as st

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────

st.set_page_config(
    page_title="Daily Market Briefing",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .market-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 4px solid #444;
    }
    .market-card.green { border-left-color: #00c853; }
    .market-card.red   { border-left-color: #ff1744; }

    .card-name  { font-size: 15px; font-weight: 600; color: #cdd6f4; }
    .card-price { font-size: 18px; font-weight: 700; color: #ffffff; }
    .card-change-green { font-size: 14px; color: #00e676; font-weight: 600; }
    .card-change-red   { font-size: 14px; color: #ff5252; font-weight: 600; }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #cba6f7;
        margin: 24px 0 12px 0;
        letter-spacing: 0.5px;
    }

    .earnings-row {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        border-left: 4px solid #89b4fa;
        color: #cdd6f4;
        font-size: 14px;
    }
    .earnings-name { font-weight: 600; color: #89dceb; }
    .earnings-date { color: #a6e3a1; font-weight: 500; }

    .timestamp {
        font-size: 13px;
        color: #6c7086;
        margin-bottom: 20px;
    }

    .stApp { background-color: #11111b; }
    div[data-testid="stVerticalBlock"] { gap: 0rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

MARKET_SYMBOLS = [
    ("^DJI",     "DOW Jones"),
    ("^GSPC",    "S&P 500"),
    ("^IXIC",    "NASDAQ"),
    ("CL=F",     "Crude Oil"),
    ("GC=F",     "Gold"),
    ("SI=F",     "Silver"),
    ("USDINR=X", "USD/INR"),
]

ASIAN_SYMBOLS = [
    ("^NSEI",    "Nifty 50"),
    ("^BSESN",   "Sensex"),
    ("^NSEBANK", "Bank Nifty"),
]

EARNINGS_STOCKS = [
    ("SBIN.NS",       "SBI"),
    ("ITC.NS",        "ITC"),
    ("WIPRO.NS",      "Wipro"),
    ("CANBK.NS",      "Canara Bank"),
    ("TATAMOTORS.NS", "Tata Motors"),
    ("MOREPENLAB.NS", "Morepen"),
    ("IOB.NS",        "IOB"),
    ("YESBANK.NS",    "Yes Bank"),
    ("PETRONET.NS",   "Petronet"),
]

# ─────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────

@st.cache_data(ttl=300)
def get_data(symbol):
    try:
        h = yf.Ticker(symbol).history(period="5d")
        if h.empty or len(h) < 2:
            return None, None, None, None
        last, prev = h.iloc[-1], h.iloc[-2]
        price = round(float(last["Close"]), 2)
        chg   = round(price - float(prev["Close"]), 2)
        pct   = round((chg / float(prev["Close"])) * 100, 2)
        dt    = h.index[-1].strftime("%d %b %Y")
        return price, chg, pct, dt
    except:
        return None, None, None, None


@st.cache_data(ttl=3600)
def get_earnings(symbol):
    try:
        t = yf.Ticker(symbol)
        cal = t.calendar
        if cal is not None and not cal.empty:
            cols = list(cal.columns)
            if cols:
                d = cols[0]
                if hasattr(d, "strftime"):
                    return d.strftime("%d %b %Y")
        try:
            ed = t.earnings_dates
            if ed is not None and not ed.empty:
                return ed.index[0].strftime("%d %b %Y")
        except:
            pass
        try:
            ts = t.info.get("earningsTimestamp")
            if ts:
                return datetime.fromtimestamp(ts).strftime("%d %b %Y")
        except:
            pass
    except:
        pass
    return "N/A"

# ─────────────────────────────────────────
# CARD RENDERER
# ─────────────────────────────────────────

def render_market_card(name, price, chg, pct, invert=False):
    if price is None:
        st.markdown(f"""
        <div class="market-card">
            <div class="card-name">{name}</div>
            <div class="card-price" style="color:#6c7086;">N/A</div>
        </div>""", unsafe_allow_html=True)
        return

    # For USD/INR: rising rate is bad for India, so invert colour logic
    is_positive  = (chg < 0) if invert else (chg >= 0)
    color_class  = "green" if is_positive else "red"
    change_class = "card-change-green" if is_positive else "card-change-red"
    arrow        = "▲" if chg >= 0 else "▼"
    sign         = "+" if chg >= 0 else ""

    st.markdown(f"""
    <div class="market-card {color_class}">
        <div class="card-name">{name}</div>
        <div>
            <div class="card-price">{price:,.2f}</div>
            <div class="{change_class}">{arrow} {sign}{chg:.2f} &nbsp;({sign}{pct:.2f}%)</div>
        </div>
    </div>""", unsafe_allow_html=True)


def render_earnings_row(name, date):
    st.markdown(f"""
    <div class="earnings-row">
        <span class="earnings-name">🔹 {name}</span>
        <span class="earnings-date">📅 {date}</span>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# MAIN UI
# ─────────────────────────────────────────

st.markdown("## 📊 Daily Market Briefing")
st.markdown(f'<div class="timestamp">🕗 {datetime.now().strftime("%d %b %Y, %H:%M IST")}</div>',
            unsafe_allow_html=True)

if st.button("🔄 Refresh Data", type="primary"):
    st.cache_data.clear()
    st.rerun()

# ── GLOBAL MARKETS ──
st.markdown('<div class="section-title">🌍 Global Markets</div>', unsafe_allow_html=True)

with st.spinner("Loading global markets..."):
    col1, col2 = st.columns(2)
    for i, (sym, name) in enumerate(MARKET_SYMBOLS):
        price, chg, pct, dt = get_data(sym)
        with (col1 if i % 2 == 0 else col2):
            render_market_card(name, price, chg, pct, invert=(name in ("USD/INR", "Crude Oil")))

# ── ASIAN MARKETS ──
st.markdown('<div class="section-title">🌏 Asian Markets Yesterday info</div>', unsafe_allow_html=True)

with st.spinner("Loading Asian markets..."):
    col1, col2 = st.columns(2)
    for i, (sym, name) in enumerate(ASIAN_SYMBOLS):
        price, chg, pct, dt = get_data(sym)
        with (col1 if i % 2 == 0 else col2):
            render_market_card(name, price, chg, pct)

