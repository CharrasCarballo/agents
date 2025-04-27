import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def percentIncrease(df):
    dfPercents = {}
    for i in df:
        mask = df[i] == 'N/A'
        df.loc[mask, i] = 0
        df[i] = pd.to_numeric(df[i], errors='coerce').fillna(0)
        vals = df[i].values
        minVal = min(vals)
        if minVal == 0:
            percents = vals
        else:
            percents = (vals - minVal) / abs(minVal)
        dfPercents[i] = percents
    dfPercents = pd.DataFrame(data=dfPercents, index=df.index)
    return dfPercents

# Function to fetch financial data including dividends and debt
def get_financials(ticker):
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        balance_sheet = stock.balance_sheet

        # Financial metrics
        ebit = financials.loc["EBIT"] if "EBIT" in financials.index else pd.Series(0, index=financials.columns)
        ebitda = financials.loc["EBITDA"] if "EBITDA" in financials.index else pd.Series(0, index=financials.columns)
        gross_profit = financials.loc["Gross Profit"] if "Gross Profit" in financials.index else pd.Series(0, index=financials.columns)
        net_income = financials.loc["Net Income"] if "Net Income" in financials.index else pd.Series(0, index=financials.columns)
        research_development = financials.loc["Research And Development"] if "Research And Development" in financials.index else pd.Series(0, index=financials.columns)
        total_revenue = financials.loc["Total Revenue"] if "Total Revenue" in financials.index else pd.Series(0, index=financials.columns)

        # Balance sheet metrics
        ordinary_shares = balance_sheet.loc["Ordinary Shares Number"] if "Ordinary Shares Number" in balance_sheet.index else pd.Series(0, index=balance_sheet.columns)
        stockholders_equity = balance_sheet.loc["Stockholders Equity"] if "Stockholders Equity" in balance_sheet.index else pd.Series(0, index=balance_sheet.columns)
        total_debt = balance_sheet.loc["Total Debt"] if "Total Debt" in balance_sheet.index else pd.Series(0, index=balance_sheet.columns)
        total_assets = balance_sheet.loc["Total Assets"] if "Total Assets" in balance_sheet.index else pd.Series(0, index=balance_sheet.columns)

        # Dividend data
        dividends = stock.dividends
        stock_price_history = stock.history(period="5y")["Close"]
        dividend_yield = []
        if not dividends.empty:
            for date in ordinary_shares.index:
                start_date = date - timedelta(days=3)
                end_date = date + timedelta(days=3)
                avg_price = np.average(stock.history(start=start_date, end=end_date)["Close"].values)
                yearly_dividend = dividends[dividends.index.year == date.year].sum() if date.year in dividends.index.year else 0
                dividend_yield.append(yearly_dividend / avg_price if avg_price != 0 else 0)
        else:
            dividend_yield = [0] * len(ordinary_shares)

        # Market cap calculation
        market_cap = []
        for day in ordinary_shares.index:
            start_date = day - timedelta(days=3)
            end_date = day + timedelta(days=3)
            stock_price = np.average(stock.history(start=start_date, end=end_date)["Close"].values)
            market_cap.append(ordinary_shares.loc[day] * stock_price)

        financials_data = {
            "EBIT": ebit,
            "EBITDA": ebitda,
            "Gross Profit": gross_profit,
            "Net Income": net_income,
            "Research And Development": research_development,
            "Total Revenue": total_revenue,
            "Ordinary Shares": ordinary_shares,
            "Stockholders Equity": stockholders_equity,
            "MarketCap": market_cap,
            "Company value perception": [mc / se if se != 0 else 0 for mc, se in zip(market_cap, stockholders_equity)],
            "Dividend Yield": dividend_yield,
            "Total Debt": total_debt,
            "Total Assets": total_assets
        }

        df_ticker = pd.DataFrame(data=financials_data, index=ordinary_shares.index)
        scale_ticker = percentIncrease(df_ticker)

        return [financials_data, scale_ticker, stock_price_history, stock.info['longName'], df_ticker, None]
    
    except Exception as e:
        return [None, None, None, f"Error: An unexpected issue occurred with '{ticker}': {str(e)}", None, str(e)]

# Streamlit UI
def main():
    st.title("Multi-Stock Financial Analyzer")
    ticker_input = st.text_input("Enter Stock Ticker Symbols (comma-separated, e.g., AAPL, MSFT, TSLA):")
    
    if st.button("Analyze Stocks"):
        if ticker_input:
            tickers = [t.strip().upper() for t in ticker_input.split(",")]
            current_date = datetime.now().strftime("%Y-%m-%d")
            zip_buffer = io.BytesIO()
            valid_data = False

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                with st.spinner("Fetching data..."):
                    for ticker in tickers:
                        st.subheader(f"Analysis for {ticker}")
                        [financials, scale_ticker, stock_price_history, company_name, df_ticker, error] = get_financials(ticker)
                        
                        if financials is None:
                            st.error(company_name)
                            continue
    
                        valid_data = True

                        # Save financials to CSV and add to ZIP
                        financials_csv = df_ticker.to_csv(index=True)
                        zip_file.writestr(f"{ticker}_{current_date}_financials.csv", financials_csv)

                        # Save price history to CSV and add to ZIP
                        price_history_df = pd.DataFrame(stock_price_history, columns=["Close"])
                        price_history_csv = price_history_df.to_csv(index=True)
                        zip_file.writestr(f"{ticker}_{current_date}_price_history.csv", price_history_csv)
    
                        # Graph 1: Scaled EBIT and EBITDA
                        st.write("**EBIT and EBITDA (Percentage Change)**")
                        plt.figure(figsize=(10, 4))
                        for metric in ["EBIT", "EBITDA"]:
                            if metric in scale_ticker.columns:
                                plt.plot(scale_ticker.index, scale_ticker[metric], label=metric)
                        plt.title(f"EBIT and EBITDA Trends for {company_name}", fontsize=12)
                        plt.xlabel("Date", fontsize=10)
                        plt.ylabel("Percentage Change", fontsize=10)
                        plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                        plt.grid(True, linestyle='--', alpha=0.7)
                        st.pyplot(plt.gcf())
                        st.write(
                            "- **EBIT**: Earnings Before Interest & Taxes.\n"
                            "- **EBITDA**: EBIT plus Depreciation and Amortization."
                        )
                        plt.clf()
    
                        # Graph 2: Scaled Gross Profit, Net Income, Total Revenue
                        st.write("**Total Revenue, Gross Profit, and Net Income (Percentage Change)**")
                        plt.figure(figsize=(10, 4))
                        for metric in ["Total Revenue", "Gross Profit", "Net Income"]:
                            if metric in scale_ticker.columns:
                                plt.plot(scale_ticker.index, scale_ticker[metric], label=metric)
                        plt.title(f"Profit and Revenue Trends for {company_name}", fontsize=12)
                        plt.xlabel("Date", fontsize=10)
                        plt.ylabel("Percentage Change", fontsize=10)
                        plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                        plt.grid(True, linestyle='--', alpha=0.7)
                        st.pyplot(plt.gcf())
                        st.write(
                            "- **Total Revenue**: Total income from operations.\n"
                            "- **Gross Profit**: Revenue minus Cost of Goods Sold.\n"
                            "- **Net Income**: Final profitability after all expenses."
                        )
                        plt.clf()
    
                        # Graph 3: Scaled Stockholders Equity, MarketCap, Ordinary Shares
                        st.write("**Equity, Market Cap, and Shares (Percentage Change)**")
                        plt.figure(figsize=(10, 4))
                        for metric in ["Stockholders Equity", "MarketCap", "Ordinary Shares"]:
                            if metric in scale_ticker.columns:
                                plt.plot(scale_ticker.index, scale_ticker[metric], label=metric)
                        plt.title(f"Equity and Market Trends for {company_name}", fontsize=12)
                        plt.xlabel("Date", fontsize=10)
                        plt.ylabel("Percentage Change", fontsize=10)
                        plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                        plt.grid(True, linestyle='--', alpha=0.7)
                        st.pyplot(plt.gcf())
                        st.write(
                            "- **Stockholders Equity**: Net asset value.\n"
                            "- **MarketCap**: Market value of shares.\n"
                            "- **Ordinary Shares**: Number of shares available."
                        )
                        plt.clf()
    
                        # Graph 4: Raw Company Value Perception
                        st.write("**Company Value Perception (Raw Data)**")
                        plt.figure(figsize=(10, 4))
                        if "Company value perception" in financials:
                            plt.plot(scale_ticker.index, financials["Company value perception"], label="Company Value Perception", color='purple')
                        plt.title(f"Company Value Perception for {company_name}", fontsize=12)
                        plt.xlabel("Date", fontsize=10)
                        plt.ylabel("Market Cap / Equity Ratio", fontsize=10)
                        plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                        plt.grid(True, linestyle='--', alpha=0.7)
                        st.pyplot(plt.gcf())
                        st.write(
                            "- **Company Value Perception**: Market Cap divided by Stockholders Equity."
                        )
                        plt.clf()
    
                        # Graph 5: Scaled Research and Development
                        st.write("**Research and Development (Percentage Change)**")
                        plt.figure(figsize=(10, 4))
                        if "Research And Development" in scale_ticker.columns:
                            plt.plot(scale_ticker.index, scale_ticker["Research And Development"], label="R&D", color='green')
                        plt.title(f"R&D Trends for {company_name}", fontsize=12)
                        plt.xlabel("Date", fontsize=10)
                        plt.ylabel("Percentage Change", fontsize=10)
                        plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                        plt.grid(True, linestyle='--', alpha=0.7)
                        st.pyplot(plt.gcf())
                        st.write(
                            "- **Research And Development**: Investment in innovation."
                        )
                        plt.clf()
    
                        # Graph 6: Dividend Yield
                        st.write("**Dividend Yield (Raw Data)**")
                        plt.figure(figsize=(10, 4))
                        if "Dividend Yield" in financials:
                            plt.plot(scale_ticker.index, financials["Dividend Yield"], label="Dividend Yield", color='orange')
                        plt.title(f"Dividend Yield for {company_name}", fontsize=12)
                        plt.xlabel("Date", fontsize=10)
                        plt.ylabel("Dividend / Stock Price", fontsize=10)
                        plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                        plt.grid(True, linestyle='--', alpha=0.7)
                        st.pyplot(plt.gcf())
                        st.write(
                            "- **Dividend Yield**: Annual dividends per share divided by stock price."
                        )
                        plt.clf()
    
                        # Graph 7: Total Debt and Total Assets
                        st.write("**Total Debt and Total Assets (Percentage Change)**")
                        plt.figure(figsize=(10, 4))
                        for metric in ["Total Debt", "Total Assets"]:
                            if metric in scale_ticker.columns:
                                plt.plot(scale_ticker.index, scale_ticker[metric], label=metric)
                        plt.title(f"Debt and Assets Trends for {company_name}", fontsize=12)
                        plt.xlabel("Date", fontsize=10)
                        plt.ylabel("Percentage Change", fontsize=10)
                        plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                        plt.grid(True, linestyle='--', alpha=0.7)
                        st.pyplot(plt.gcf())
                        st.write(
                            "- **Total Debt**: Sum of short-term and long-term liabilities.\n"
                            "- **Total Assets**: Total value of company’s resources."
                        )
                        plt.clf()
    
                        # Graph 8: Stock Price Trend
                        st.write("**Stock Price Trend**")
                        plt.figure(figsize=(10, 4))
                        plt.plot(stock_price_history.index, stock_price_history, label="Closing Price", color='blue')
                        plt.title(f"5-Year Stock Price History for {company_name}", fontsize=12)
                        plt.xlabel("Date", fontsize=10)
                        plt.ylabel("Stock Price (USD)", fontsize=10)
                        plt.legend(title="Price", bbox_to_anchor=(1.05, 1), loc='upper left')
                        plt.grid(True, linestyle='--', alpha=0.7)
                        st.pyplot(plt.gcf())
                        plt.clf()

            # Provide download button for the ZIP file if there is valid data
            if valid_data:
                zip_buffer.seek(0)
                st.write("**Download All Data**")
                st.download_button(
                    label=f"Download All Financials and Price Histories ({current_date})",
                    data=zip_buffer,
                    file_name=f"stock_data_{current_date}.zip",
                    mime="application/zip"
                )

            else:
                st.error("No valid data to download. Please check the ticker symbols.")
        else:
            st.error("Please enter at least one valid stock ticker.")

if __name__ == "__main__":
    main()
