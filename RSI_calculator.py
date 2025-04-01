import streamlit as st
import yfinance as yf
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Function to calculate RSI
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Get stock data
def get_stock_data(symbol, interval, days):
    ticker = yf.Ticker(symbol)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    df = ticker.history(start=start_date, end=end_date, interval=interval)
    if df.empty:
        return None
    return df['Close']

# Get crypto data
def get_crypto_data(symbol, interval, days):
    # Try using multiple exchanges with fallback options
    exchanges = ['kucoin', 'kraken', 'coinbase']
    
    timeframe_map = {'1h': '1h', '1d': '1d', '4h': '4h', '1w': '1w'}
    since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    limit = days * 24 if interval == '1h' else days * 6 if interval == '4h' else days
    
    # Formatted symbol
    formatted_symbol = f"{symbol.upper()}/USDT"  # Assuming USDT pair
    
    # Try each exchange
    for exchange_id in exchanges:
        try:
            exchange = getattr(ccxt, exchange_id)()
            exchange.load_markets()
            
            # Check if the symbol is available on this exchange
            if formatted_symbol not in exchange.symbols:
                print(f"{formatted_symbol} not available on {exchange_id}, trying another exchange...")
                continue
                
            ohlcv = exchange.fetch_ohlcv(
                formatted_symbol, 
                timeframe=timeframe_map[interval], 
                since=since, 
                limit=limit
            )
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            print(f"Successfully fetched data from {exchange_id}")
            return df['close']
            
        except Exception as e:
            print(f"Error with {exchange_id}: {str(e)}")
    
    # If all exchanges fail, fall back to yfinance
    try:
        print("Trying yfinance as fallback...")
        # Convert interval to yfinance format
        yf_interval_map = {'1h': '1h', '4h': '4h', '1d': '1d', '1w': '1wk'}
        ticker = f"{symbol}-USD"  # yfinance format
        
        data = yf.download(
            ticker,
            period=f"{days}d",
            interval=yf_interval_map[interval],
            progress=False
        )
        
        if len(data) > 0:
            print("Successfully fetched data from yfinance")
            return data['Close']
        else:
            raise Exception("No data returned from yfinance")
            
    except Exception as e:
        error_msg = f"Error fetching crypto data from all sources: {str(e)}"
        print(error_msg)
        if 'st' in globals():  # Check if streamlit is available
            st.error(error_msg)
        return None

# Plot RSI
def plot_rsi(prices, rsi):
    fig = go.Figure()
    
    # Price plot
    fig.add_trace(go.Scatter(x=prices.index, y=prices, name='Price', yaxis='y1'))
    
    # RSI plot
    fig.add_trace(go.Scatter(x=rsi.index, y=rsi, name='RSI', yaxis='y2'))
    fig.add_hline(y=70, line_dash="dash", line_color="red", yref='y2')
    fig.add_hline(y=30, line_dash="dash", line_color="green", yref='y2')
    
    # Update layout with dual y-axes
    fig.update_layout(
        title='Price and RSI',
        yaxis=dict(title='Price'),
        yaxis2=dict(title='RSI', overlaying='y', side='right', range=[0, 100]),
        height=600
    )
    
    return fig

# Streamlit app
def main():
    st.title("RSI Calculator and Visualizer")
    
    # User inputs
    symbol = st.text_input("Enter Symbol (e.g., AAPL for stock, XRP for crypto)", "AAPL")
    asset_type = st.selectbox("Asset Type", ["Stock", "Crypto"])
    interval = st.selectbox("Price Frequency", 
                          ["1d", "1h", "4h", "1w"] if asset_type == "Crypto" else ["1d"])
    days = st.slider("Number of Days", 7, 90, 30)
    rsi_period = st.slider("RSI Period", 5, 30, 14)
    
    if st.button("Calculate RSI"):
        # Fetch data based on asset type
        if asset_type == "Stock":
            prices = get_stock_data(symbol, interval, days)
        else:
            prices = get_crypto_data(symbol, interval, days)
        
        if prices is None or prices.empty:
            st.error("Could not fetch data. Please check the symbol and try again.")
            return
        
        # Calculate RSI
        rsi = calculate_rsi(prices, rsi_period)
        
        # Create results DataFrame
        results = pd.DataFrame({
            'Price': prices,
            'RSI': rsi
        })
        
        # Display results
        st.write("Last 5 entries:")
        st.dataframe(results.tail())
        
        # Plot
        fig = plot_rsi(prices, rsi)
        st.plotly_chart(fig)
        
        # Download option
        csv = results.to_csv()
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f"{symbol}_rsi.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
