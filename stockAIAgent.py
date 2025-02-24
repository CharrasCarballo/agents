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
        vals = df[i].values
        minVal = min(vals)
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

    researchAndDevelopment = financials.loc["Research And Development"] if "Research And Development" in stock.quarterly_financials.index else "N/A"

    totalRevenue = financials.loc["Total Revenue"] if "Total Revenue" in stock.quarterly_financials.index else "N/A"
    # Total amount of money the company made from all its operations (product sales, services, etc.) before any costs or expenses are deducted.

    balance_sheet = stock.balance_sheet

    ordinaryShares = balance_sheet.loc["Ordinary Shares Number"] if "Ordinary Shares Number" in stock.quarterly_balance_sheet.index else "N/A"
    #Shares Outstanding → Number of shares currently held by investors (excludes treasury shares). Ordinary shares is the same as Shares outstanding per quarter.
    #Treasury Stock → Shares the company bought back and holds in reserve (not available for public trading).

    stockHoldersEquity = balance_sheet.loc["Stockholders Equity"] if "Stockholders Equity" in stock.quarterly_balance_sheet.index else "N/A"
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
    company_name = st.text_input("Enter Company Name:")
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
            
            # Display financials
            st.subheader("Financial Overview")
            plt.figure(figsize=(10, 4))
            plt.plot(scaleTicker)
            plt.legend(companyName)
            st.pyplot(plt)

            # Display stock price trend
            st.subheader("Stock Price Trend")
            plt.figure(figsize=(10, 4))
            plt.plot(stockPriceHistory)
            plt.legend("Stock Price")
            st.pyplot(plt)
            
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
