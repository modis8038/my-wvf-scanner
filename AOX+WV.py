import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Web Page Setup
st.set_page_config(page_title="WVF Near 0 Scanner with Time", layout="wide")
st.title("💥 WVF <= 0.05 Filtered - Multi-Signal Time Scanner")
st.write("Displays all exact IST timestamps when a stock met the WVF condition during the selected day.")

# Your Custom Stock List
stocks = [
    "SHRIRAMFIN.NS", "CDSL.NS", "PRESTIGE.NS", "PERSISTENT.NS", "DIXON.NS", 
    "BSE.NS", "MCX.NS", "INFY.NS", "HCLTECH.NS", "TECHM.NS", 
    "M&M.NS", "MARUTI.NS", "AMBER.NS", "POLYCAB.NS", "TRENT.NS", 
    "SRF.NS", "AUROPHARMA.NS", "SUNPHARMA.NS", "CIPLA.NS", "DIVISLAB.NS", 
    "TITAN.NS", "CUMMINSIND.NS", "LT.NS", "ADANIENT.NS", "ADANIPORTS.NS", 
    "HAL.NS", "HINDUNILVR.NS", "BHARTIARTL.NS", "BHARATFORG.NS", "CHOLAFIN.NS", 
    "HAVELLS.NS", "VOLTAS.NS", "INDIGO.NS", "COFORGE.NS", "LUPIN.NS", 
    "HINDALCO.NS", "KEI.NS", "EICHERMOT.NS", "OBEROIRLTY.NS", "MUTHOOTFIN.NS", 
    "TVSMOTOR.NS", "HEROMOTOCO.NS", "DMART.NS", "RELIANCE.NS", "AXISBANK.NS", 
    "KOTAKBANK.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "ULTRACEMCO.NS", "ASIANPAINT.NS", 
    "NTPC.NS", "POWERGRID.NS", "TATAPOWER.NS", "JSWSTEEL.NS", "ONGC.NS", 
    "COALINDIA.NS", "GRASIM.NS", "TATACONSUM.NS", "NESTLEIND.NS", "APOLLOHOSP.NS", 
    "SIEMENS.NS", "BPCL.NS", "DRREDDY.NS"
]

# --- Sidebar Controls ---
pd_period = st.sidebar.slider("WVF LookBack Period (5m Bars)", min_value=10, max_value=50, value=22)

# Slider: 0 means Today, 1 means Yesterday, etc.
days_back = st.sidebar.slider("Select Target Trading Day (0=Today, 1=Yesterday, 4=4 Days Ago)", min_value=0, max_value=10, value=0)
fetch_period = f"{days_back + 5}d" 

results = []

with st.spinner('Scanning intraday timestamps...'):
    try:
        all_data = yf.download(stocks, period=fetch_period, interval="5m", group_by='ticker', progress=False)
        
        for symbol in stocks:
            if symbol not in all_data.columns.levels[0]:
                continue
                
            df = all_data[symbol].dropna().copy()
            if len(df) < pd_period + 5:
                continue
            
            # Convert Index to Indian Standard Time (IST) Zone
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
            else:
                df.index = df.index.tz_convert('Asia/Kolkata')
                
            df['DateOnly'] = df.index.date
            unique_dates = sorted(df['DateOnly'].unique())
            
            target_day_idx = -(days_back + 1)
            if len(unique_dates) < abs(target_day_idx) + 1:
                continue 
            
            target_date = unique_dates[target_day_idx]
            prev_date = unique_dates[target_day_idx - 1]
            
            # --- Green Box Logic ---
            df_prev_day = df[df['DateOnly'] == prev_date]
            if df_prev_day.empty:
                continue
            d_high = df_prev_day['High'].max()
            d_low = df_prev_day['Low'].min()
            up_box_top = d_high + (0.29 * (d_high - d_low))
            
            # --- WVF Intraday Window Processing ---
            df_sliced = df[df['DateOnly'] <= target_date].copy()
            
            rolling_max = df_sliced['Close'].rolling(window=pd_period).max()
            df_sliced['WVF'] = ((rolling_max - df_sliced['Low']) / rolling_max) * 100
            
            df_target_day_bars = df_sliced[df_sliced['DateOnly'] == target_date]
            
            for timestamp, bar in df_target_day_bars.iterrows():
                wvf_val = bar['WVF']
                
                if pd.notna(wvf_val) and wvf_val <= 0.05:
                    cur_high = bar['High']
                    cur_low = bar['Low']
                    
                    touch_green = (cur_high >= up_box_top) and (cur_low <= up_box_top)
                    status = "💥 MATCHED" if touch_green else "WVF 0 Only"
                    
                    # Clean IST time formatting
                    time_str = timestamp.strftime('%I:%M %p')
                    date_str = timestamp.strftime('%Y-%m-%d')
                    
                    results.append({
                        "Stock Name": symbol.replace(".NS", ""),
                        "Signal Date": date_str,
                        "Signal Time (IST)": time_str,
                        "WVF Value": round(wvf_val, 4),
                        "Status": status
                    })
            
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Display Results Table
if results:
    res_df = pd.DataFrame(results)
    
    # Sort chronologically by time
    res_df = res_df.sort_values(by=["Signal Date", "Signal Time (IST)"], ascending=[False, True]).reset_index(drop=True)

    def highlight_status(val):
        if val == "💥 MATCHED":
            return 'background-color: green; color: white; font-weight: bold;'
        elif val == "WVF 0 Only":
            return 'background-color: #333300; color: white;'
        return ''

    styled_df = res_df.style.map(highlight_status, subset=['Status'])
    st.dataframe(styled_df, width="stretch")
else:
    st.info(f"🎯 No WVF signals occurred on the selected day ({days_back} day(s) ago).")
