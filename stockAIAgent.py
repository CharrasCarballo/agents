import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from openai import OpenAI
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
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
          percents = (vals-minVal)/abs(minVal)
        dfPercents[i] = percents

    dfPercents = pd.DataFrame(data = dfPercents,
                              index = df.index)
    return dfPercents

# Set your OpenAI API key
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# Function to fetch financial data
def get_financials(ticker):

  try:

    stock = yf.Ticker(ticker)

    financials = stock.financials

    ebit = financials.loc["EBIT"] if "EBIT" in financials.index else "N/A"          #EBIT = Net Income + Interest Expense + Taxes (Earnings Before Interest & Taxes)
    #EBIT is used to evaluate a company’s core profitability from its business operations, without considering tax strategies or financing choices (debt vs. equity).

    ebitda = financials.loc["EBITDA"] if "EBITDA" in financials.index else "N/A"    #EBITDA = EBIT} + Depreciation} + Amortization (Earnings Before Interest, Taxes, Depreciation & Amortization)
    #EBITDA measures a company’s profitability before non-cash expenses (depreciation & amortization) and financial decisions (interest & taxes).

    grossProfit = financials.loc["Gross Profit"] if "Gross Profit" in financials.index else "N/A"
    #Gross Profit = Revenue - Cost of Goods Sold; How much is left after subtracting the direct cost of producing goods/services

    netIncome = financials.loc["Net Income"] if "Net Income" in financials.index else "N/A"
    #Net Income = Total Revenue - Cost of Goods Sold + Operating Expenses + Interest Expense + Taxes + Any Other Costs
    #It represents the final measure of profitability—i.e., what’s left for shareholders or reinvestment after every cost is paid.

    researchAndDevelopment = financials.loc["Research And Development"] if "Research And Development" in financials.index else "N/A"

    totalRevenue = financials.loc["Total Revenue"] if "Total Revenue" in financials.index else "N/A"
    # Total amount of money the company made from all its operations (product sales, services, etc.) before any costs or expenses are deducted.

    balance_sheet = stock.balance_sheet

    ordinaryShares = balance_sheet.loc["Ordinary Shares Number"] if "Ordinary Shares Number" in balance_sheet.index else "N/A"
    #Shares Outstanding → Number of shares currently held by investors (excludes treasury shares). Ordinary shares is the same as Shares outstanding per quarter.
    #Treasury Stock → Shares the company bought back and holds in reserve (not available for public trading).

    stockHoldersEquity = balance_sheet.loc["Stockholders Equity"] if "Stockholders Equity" in balance_sheet.index else "N/A"
    #The Book Value of a company represents its net asset value, or how much the company would be worth if it sold all its assets and paid off all its liabilities.
    #The Book value is the same as Stockholders Equity.

    stockPriceHistory = stock.history(period="5y")["Close"]

    marketCap = []

    for day in ordinaryShares.index:
      
      startDate = day - timedelta(days=3)
      endDate = day + timedelta(days=3)
      stockPrice = np.average(stock.history(start = startDate, end = endDate)["Close"].values)
      marketCap.append(ordinaryShares.loc[day] * stockPrice)

    financials = {
        "EBIT": ebit,
        "EBITDA": ebitda,
        "Gross Profit": grossProfit,
        "Net Income": netIncome,
        "Research And Development": researchAndDevelopment,
        "Total Revenue": totalRevenue,
        "Ordinary Shares": ordinaryShares,
        "Stockholders Equity": stockHoldersEquity,
        "MarketCap": marketCap,
        "Company value perception": marketCap/stockHoldersEquity
    }

    dfTicker = pd.DataFrame(data = financials, index = ordinaryShares.index)
    scaleTicker = percentIncrease(dfTicker)

    return [financials, scaleTicker, stockPriceHistory, stock.info['longName']]
  
  except Exception as e:
    return [None, None, None, f"Error: An unexpected issue occurred with '{ticker}': {str(e)}"]

# Function to compare with competitors
# def get_competitor_data(ticker):
#     stock = yf.Ticker(ticker)
#     competitors = stock.info.get("industry")
#     return competitors  # Placeholder for competitor analysis

# # Function to analyze executive team
# def get_executive_data(ticker):
#     stock = yf.Ticker(ticker)
#     return stock.info.get("companyOfficers", [])

# # Function to generate AI insights
# def get_ai_insights(company_name):
#     prompt = f"""Analyze the financial health, future prospects, and challenges for {company_name}.
#     Consider its recent earnings, industry trends, and executive leadership."""

#     response = client.chat.completions.create(
#         model="gpt-4",
#         messages=[
#             {"role": "system", "content": "You are a financial analyst."},
#             {"role": "user", "content": prompt}
#         ]
#     )

#     return response.choices[0].message.content

# # Function to fetch real-time news
# def get_latest_news(company_name):
#     url = f"https://newsapi.org/v2/everything?q={company_name}&apiKey={NEWS_API_KEY}"
#     response = requests.get(url).json()
#     articles = response.get("articles", [])[:5]
#     return [{"title": article["title"], "url": article["url"]} for article in articles]

# # Function to predict stock price
# def predict_stock_price(ticker):
#     stock = yf.Ticker(ticker)
#     hist = stock.history(period="1y")["Close"]
#     forecast = hist.rolling(window=5).mean().iloc[-1]  # Simple moving average prediction
#     return forecast

# Streamlit UI
def main():
    st.title("AI Stock Investment Advisor")
    #company_name = st.text_input("Enter Company Name:")
    ticker = st.text_input("Enter Stock Ticker Symbol:")
    
    if st.button("Analyze Stock"):
        if ticker:
            with st.spinner("Fetching data..."):
                [financials, scaleTicker, stockPriceHistory, companyName] = get_financials(ticker)
                # competitors = get_competitor_data(ticker)
                # executives = get_executive_data(ticker)
                # insights = get_ai_insights(company_name)
                # news = get_latest_news(company_name)
                # predicted_price = predict_stock_price(ticker)

            if financials is None:
                st.error(companyName)  # Display the error message
            else:
                # Graph 1: Scaled EBIT and EBITDA
                st.subheader("EBIT and EBITDA (Percentage Change)")
                plt.figure(figsize=(10, 4))
                for metric in ["EBIT", "EBITDA"]:
                    if metric in scaleTicker.columns:
                        plt.plot(scaleTicker.index, scaleTicker[metric], label=metric)
                plt.title(f"EBIT and EBITDA Trends for {companyName}", fontsize=12)
                plt.xlabel("Date", fontsize=10)
                plt.ylabel("Percentage Change", fontsize=10)
                plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.grid(True, linestyle='--', alpha=0.7)
                st.pyplot(plt.gcf())
                st.write(
                    "- **EBIT**: Net Income + Interest Expense + Taxes (Earnings Before Interest & Taxes). EBIT is used to evaluate "
                    "a company’s core profitability from its business operations, without considering tax strategies or financing "
                    "choices (debt vs. equity).\n"
                    "- **EBITDA**: EBIT plus Depreciation and Amortization, reflecting cash flow potential before non-cash expenses."
                    "EBITDA measures a company’s profitability before non-cash expenses (depreciation & amortization) and financial decisions (interest & taxes)."
                )
                plt.clf()

                # Graph 2: Scaled Gross Profit, Net Income, Total Revenue
                st.subheader("Total Revenue, Gross Profit and Net Income (Percentage Change)")
                plt.figure(figsize=(10, 4))
                for metric in ["Total Revenue", "Gross Profit", "Net Income"]:
                    if metric in scaleTicker.columns:
                        plt.plot(scaleTicker.index, scaleTicker[metric], label=metric)
                plt.title(f"Profit and Revenue Trends for {companyName}", fontsize=12)
                plt.xlabel("Date", fontsize=10)
                plt.ylabel("Percentage Change", fontsize=10)
                plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.grid(True, linestyle='--', alpha=0.7)
                st.pyplot(plt.gcf())
                st.write(
                    "- **Total Revenue**: Total amount of money the company made from all its operations (product sales, services, etc.) before any costs or expenses are deducted.\n"
                    "- **Gross Profit**: Revenue - Cost of Goods Sold; How much is left after subtracting the direct cost of producing goods/services\n"
                    "- **Net Income**: Total Revenue - (Cost of Goods Sold + Operating Expenses + Interest Expense + Taxes + Any Other Costs). It represents "
                    "the final measure of profitability—i.e., what’s left for shareholders or reinvestment after every cost is paid."
                )
                plt.clf()

                # Graph 3: Scaled Stockholders Equity, MarketCap, Ordinary Shares
                st.subheader("Equity, Market Cap, and Shares (Percentage Change)")
                plt.figure(figsize=(10, 4))
                for metric in ["Stockholders Equity", "MarketCap", "Ordinary Shares"]:
                    if metric in scaleTicker.columns:
                        plt.plot(scaleTicker.index, scaleTicker[metric], label=metric)
                plt.title(f"Equity and Market Trends for {companyName}", fontsize=12)
                plt.xlabel("Date", fontsize=10)
                plt.ylabel("Percentage Change", fontsize=10)
                plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.grid(True, linestyle='--', alpha=0.7)
                st.pyplot(plt.gcf())
                st.write(
                    "- **Stockholders Equity**: Net asset value (assets minus liabilities), or book value, or how much the company would be worth if it sold all its assets and paid off all its liabilities.\n"
                    "- **MarketCap**: Market value of all shares, reflecting investor perception.\n"
                    "- **Ordinary Shares**: Number of shares available, affecting ownership dilution."
                )
                plt.clf()

                # Graph 4: Raw Company Value Perception
                st.subheader("Company Value Perception (Raw Data)")
                plt.figure(figsize=(10, 4))
                if "Company value perception" in financials:
                    plt.plot(scaleTicker.index, financials["Company value perception"], label="Company Value Perception", color='purple')
                plt.title(f"Company Value Perception for {companyName}", fontsize=12)
                plt.xlabel("Date", fontsize=10)
                plt.ylabel("Market Cap / Equity Ratio", fontsize=10)
                plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.grid(True, linestyle='--', alpha=0.7)
                st.pyplot(plt.gcf())
                st.write(
                    "- **Company Value Perception**: Market Cap divided by Stockholders Equity, indicating how the market values the company relative to its book value."
                )
                plt.clf()

                # Graph 5: Scaled Research and Development
                st.subheader("Research and Development (Percentage Change)")
                plt.figure(figsize=(10, 4))
                if "Research And Development" in scaleTicker.columns:
                    plt.plot(scaleTicker.index, scaleTicker["Research And Development"], label="R&D", color='green')
                plt.title(f"R&D Trends for {companyName}", fontsize=12)
                plt.xlabel("Date", fontsize=10)
                plt.ylabel("Percentage Change", fontsize=10)
                plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.grid(True, linestyle='--', alpha=0.7)
                st.pyplot(plt.gcf())
                st.write(
                    "- **Research And Development**: Investment in innovation and future growth, showing commitment to new products or services."
                )
                plt.clf()
                
                # Display stock price trend
                st.subheader("Stock Price Trend")
                plt.figure(figsize=(10, 4))
                plt.plot(stockPriceHistory.index, stockPriceHistory, label="Closing Price", color='blue')
                plt.title(f"5-Year Stock Price History for {companyName}", fontsize=12)
                plt.xlabel("Date", fontsize=10)
                plt.ylabel("Stock Price (USD)", fontsize=10)
                plt.legend(title="Price", bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.grid(True, linestyle='--', alpha=0.7)
                st.pyplot(plt.gcf())
                plt.clf()  # Clear the figure
            
            # # Competitor Analysis
            # st.subheader("Competitor Analysis")
            # st.write(competitors)
            
            # # Executive Team Report
            # st.subheader("Executive Team")
            # for exec in executives:
            #     st.write(f"**{exec['name']}** - {exec['title']}")
            
            # # AI-Generated Insights
            # st.subheader("AI Investment Insights")
            # st.write(insights)
            
            # # Real-time News
            # st.subheader("Latest News")
            # for article in news:
            #     st.write(f"[{article['title']}]({article['url']})")
            
            # # Stock Price Prediction
            # st.subheader("Stock Price Prediction")
            # st.write(f"Predicted Stock Price (based on trend analysis): ${predicted_price:.2f}")
        else:
            st.error("Please enter a valid stock ticker.")

if __name__ == "__main__":
    main()
