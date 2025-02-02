import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from openai import OpenAI
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Set your OpenAI API key
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# Function to fetch financial data
def get_financials(ticker):
    stock = yf.Ticker(ticker)
    financials = {
        "Revenue": stock.financials.loc["Total Revenue"],
        "Net Income": stock.financials.loc["Net Income"],
        "EPS": stock.financials.loc["Diluted EPS"],
        "Stock Price History": stock.history(period="5y")["Close"],
    }
    return financials

# Function to compare with competitors
def get_competitor_data(ticker):
    stock = yf.Ticker(ticker)
    competitors = stock.info.get("industry")
    return competitors  # Placeholder for competitor analysis

# Function to analyze executive team
def get_executive_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.info.get("companyOfficers", [])

# Function to generate AI insights
def get_ai_insights(company_name):
    prompt = f"""Analyze the financial health, future prospects, and challenges for {company_name}.
    Consider its recent earnings, industry trends, and executive leadership."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a financial analyst."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# Function to fetch real-time news
def get_latest_news(company_name):
    url = f"https://newsapi.org/v2/everything?q={company_name}&apiKey={NEWS_API_KEY}"
    response = requests.get(url).json()
    articles = response.get("articles", [])[:5]
    return [{"title": article["title"], "url": article["url"]} for article in articles]

# Function to predict stock price
def predict_stock_price(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")["Close"]
    forecast = hist.rolling(window=5).mean().iloc[-1]  # Simple moving average prediction
    return forecast

# Streamlit UI
def main():
    st.title("AI Stock Investment Advisor")
    company_name = st.text_input("Enter Company Name:")
    ticker = st.text_input("Enter Stock Ticker Symbol:")

    st.write(OPENAI_API_KEY)
    st.write(NEWS_API_KEY)
    
    if st.button("Analyze Stock"):
        if ticker:
            with st.spinner("Fetching data..."):
                financials = get_financials(ticker)
                competitors = get_competitor_data(ticker)
                executives = get_executive_data(ticker)
                insights = get_ai_insights(company_name)
                news = get_latest_news(company_name)
                predicted_price = predict_stock_price(ticker)
            
            # Display financials
            st.subheader("Financial Overview")
            st.write(financials)
            
            # Display stock price trend
            st.subheader("Stock Price Trend")
            plt.figure(figsize=(10, 4))
            plt.plot(financials["Stock Price History"], label=ticker)
            plt.legend()
            st.pyplot(plt)
            
            # Competitor Analysis
            st.subheader("Competitor Analysis")
            st.write(competitors)
            
            # Executive Team Report
            st.subheader("Executive Team")
            for exec in executives:
                st.write(f"**{exec['name']}** - {exec['title']}")
            
            # AI-Generated Insights
            st.subheader("AI Investment Insights")
            st.write(insights)
            
            # Real-time News
            st.subheader("Latest News")
            for article in news:
                st.write(f"[{article['title']}]({article['url']})")
            
            # Stock Price Prediction
            st.subheader("Stock Price Prediction")
            st.write(f"Predicted Stock Price (based on trend analysis): ${predicted_price:.2f}")
        else:
            st.error("Please enter a valid stock ticker.")

if __name__ == "__main__":
    main()
