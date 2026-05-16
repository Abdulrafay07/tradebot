import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd

st.set_page_config(page_title="Pro Trade Signals", layout="wide")

def get_signals(ticker, asset_type):
    # Fetch 1-hour data for Day/Swing Trading
    df = yf.download(ticker, period="1mo", interval="1h", progress=False)
    if df.empty: return None
    
    # 1. Trend Logic (Crypto) - EMA Cross
    if asset_type == "Crypto":
        df['EMA_fast'] = ta.ema(df['Close'], length=20)
        df['EMA_slow'] = ta.ema(df['Close'], length=50)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        if prev['EMA_fast'] < prev['EMA_slow'] and last['EMA_fast'] > last['EMA_slow']:
            signal = "BUY"
        elif prev['EMA_fast'] > prev['EMA_slow'] and last['EMA_fast'] < last['EMA_slow']:
            signal = "SELL"
        else:
            signal = "NEUTRAL"

    # 2. Mean Reversion Logic (Forex) - Bollinger Bands
    else:
        bbands = ta.bbands(df['Close'], length=20, std=2)
        df = pd.concat([df, bbands], axis=1)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        last = df.iloc[-1]
        
        if last['Close'] < last['BBL_20_2.0'] and last['RSI'] < 35:
            signal = "BUY"
        elif last['Close'] > last['BBU_20_2.0'] and last['RSI'] > 65:
            signal = "SELL"
        else:
            signal = "NEUTRAL"

    # Risk Management Calculation (ATR based)
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    atr = df['ATR'].iloc[-1]
    price = df['Close'].iloc[-1]
    
    sl = price - (atr * 2) if signal == "BUY" else price + (atr * 2)
    tp = price + (atr * 4) if signal == "BUY" else price - (atr * 4)
    
    return {"ticker": ticker, "signal": signal, "price": price, "sl": sl, "tp": tp}

# --- UI Layout ---
st.title("🚀 Multi-Market Signal Dashboard")
st.write("Targeting Crypto Swing and Forex Day Trades.")

col1, col2 = st.columns(2)

with col1:
    st.header("Crypto (BTC/ETH)")
    for ticker in ["BTC-USD", "ETH-USD"]:
        res = get_signals(ticker, "Crypto")
        if res:
            color = "green" if res['signal'] == "BUY" else "red" if res['signal'] == "SELL" else "gray"
            st.subheader(f"{ticker}: :{color}[{res['signal']}]")
            st.write(f"Price: **${res['price']:,.2f}**")
            if res['signal'] != "NEUTRAL":
                st.success(f"Target TP: {res['tp']:.2f} | Stop Loss: {res['sl']:.2f}")

with col2:
    st.header("Forex (EUR/GBP/JPY)")
    for ticker in ["EURUSD=X", "GBPUSD=X", "USDJPY=X"]:
        res = get_signals(ticker, "Forex")
        if res:
            color = "green" if res['signal'] == "BUY" else "red" if res['signal'] == "SELL" else "gray"
            st.subheader(f"{ticker}: :{color}[{res['signal']}]")
            st.write(f"Price: **{res['price']:.4f}**")
            if res['signal'] != "NEUTRAL":
                st.success(f"Target TP: {res['tp']:.4f} | Stop Loss: {res['sl']:.4f}")