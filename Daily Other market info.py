# pip install yfinance selenium webdriver-manager

import time, os, urllib.parse
from datetime import datetime
import yfinance as yf

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.binary_location = "/usr/bin/chromium"

driver = webdriver.Chrome(options=options)

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

WHATSAPP_PHONE = "11111111"

MARKET_SYMBOLS = [
    ("^DJI",     "DOW"),
    ("^GSPC",    "S&P500"),
    ("^IXIC",    "NASDAQ"),
    ("CL=F",     "Crude"),
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
    ("SBIN.NS",      "SBI"),
    ("ITC.NS",       "ITC"),
    ("WIPRO.NS",     "Wipro"),
    ("CANBK.NS",     "Canara"),
    ("TMPV.NS",      "Tata Motors PV"),
    ("MOREPENLAB.NS","Morepen"),
    ("IOB.NS",       "IOB"),
    ("YESBANK.NS",   "Yes Bank"),
    ("PETRONET.NS",  "Petronet"),
]

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def get_data(symbol):
    try:
        h = yf.Ticker(symbol).history(period="5d")
        if h.empty or len(h) < 2:
            return None, None, None, None

        last, prev = h.iloc[-1], h.iloc[-2]

        price = round(last["Close"], 2)
        chg   = round(price - prev["Close"], 2)
        pct   = round((chg / prev["Close"]) * 100, 2)
        dt    = h.index[-1].strftime("%d %b %Y")

        return price, chg, pct, dt
    except:
        return None, None, None, None


def get_earnings(symbol):
    try:
        t = yf.Ticker(symbol)

        # 1️⃣ calendar
        cal = t.calendar
        if cal is not None and not cal.empty:
            cols = list(cal.columns)
            if cols:
                d = cols[0]
                if hasattr(d, "strftime"):
                    return d.strftime("%d %b %Y")

        # 2️⃣ earnings_dates
        try:
            ed = t.earnings_dates
            if ed is not None and not ed.empty:
                d = ed.index[0]
                return d.strftime("%d %b %Y")
        except:
            pass

        # 3️⃣ info fallback
        try:
            info = t.info
            ts = info.get("earningsTimestamp")
            if ts:
                return datetime.fromtimestamp(ts).strftime("%d %b %Y")
        except:
            pass

    except:
        pass

    return "N/A"


# ─────────────────────────────────────────
# MESSAGE BUILDER
# ─────────────────────────────────────────

def build_message():
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    lines = []
    lines.append("📊 *Daily Market Briefing*")
    lines.append(f"🕗 {now}\n")

    # ── GLOBAL ──
    lines.append("🌍 *GLOBAL MARKETS*")
    lines.append("┌──────────────────────────────────────┐")

    red, green = [], []

    for sym, name in MARKET_SYMBOLS:
        price, chg, pct, dt = get_data(sym)
        if price is None:
            continue

        arrow = "▲" if chg >= 0 else "▼"
        sign  = "+" if chg >= 0 else ""
        row   = f"{name:<10} {price:>9,.2f} {arrow}{sign}{chg:.2f} ({sign}{pct:.2f}%)"

        # USD/INR: rising rate is bad for India (red)
        if name == "USD/INR":
            (red if chg > 0 else green).append(f"│ {'🔴' if chg > 0 else '🟢'} {row}")
        else:
            (green if chg >= 0 else red).append(f"│ {'🟢' if chg >= 0 else '🔴'} {row}")

    lines.append("│ Market     Price      Change        │")
    lines.append("├──────────────────────────────────────┤")
    lines.extend(red)
    if red and green:
        lines.append("├──────────────────────────────────────┤")
    lines.extend(green)
    lines.append("└──────────────────────────────────────┘\n")

    # ── ASIAN ──
    lines.append("🌏 *ASIAN MARKETS*")
    lines.append("┌──────────────────────────────────────┐")

    red, green = [], []

    for sym, name in ASIAN_SYMBOLS:
        price, chg, pct, dt = get_data(sym)
        if price is None:
            continue

        arrow = "▲" if chg >= 0 else "▼"
        sign  = "+" if chg >= 0 else ""
        row   = f"{name:<10} {price:>9,.2f} {arrow}{sign}{chg:.2f} ({sign}{pct:.2f}%)"

        (green if chg >= 0 else red).append(f"│ {'🟢' if chg >= 0 else '🔴'} {row}")

    lines.append("│ Index      Price      Change        │")
    lines.append("├──────────────────────────────────────┤")
    lines.extend(red)
    if red and green:
        lines.append("├──────────────────────────────────────┤")
    lines.extend(green)
    lines.append("└──────────────────────────────────────┘\n")

    # ── EARNINGS ──
    lines.append("📅 *UPCOMING EARNINGS*")
    lines.append("────────────────────────")

    for sym, name in EARNINGS_STOCKS:
        ed = get_earnings(sym)
        lines.append(f"🔹 {name:<14} : {ed}")

    return "\n".join(lines)


# ─────────────────────────────────────────
# WHATSAPP
# ─────────────────────────────────────────

def init_browser():
    options = Options()
    options.add_argument("--start-maximized")

    session_dir = os.path.join(os.path.expanduser("~"), "whatsapp_chrome_session")
    options.add_argument(f"--user-data-dir={session_dir}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.get("https://web.whatsapp.com")

    WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="Chat list"]'))
    )

    return driver


def send_whatsapp(driver, phone, msg):
    driver.get(f"https://web.whatsapp.com/send?phone={phone}&text={urllib.parse.quote(msg)}")

    box = WebDriverWait(driver, 40).until(
        EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
    )

    time.sleep(3)
    box.send_keys(Keys.ENTER)

    print("✅ Sent")
    time.sleep(5)


# ─────────────────────────────────────────

def main():
    print("🚀 Sending Market Briefing...")

    driver = init_browser()
    msg = build_message()

    print(msg)
    send_whatsapp(driver, WHATSAPP_PHONE, msg)

    print("🎉 DONE")


if __name__ == "__main__":
    main()
