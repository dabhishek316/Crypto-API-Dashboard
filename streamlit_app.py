import altair as alt
import pandas as pd
import streamlit as st
import pandas as pd
import hmac
import hashlib
import json
import time
import requests
# Generating a timestamp.
timeStamp = int(round(time.time() * 1000))

# Access variables

key = st.secrets["key"]
secret = st.secrets["secret"]

if not key or not secret:
    raise Exception("API key or Secret key not found in environment variables")
 
body = {
    "orders_create": {
        "side": "buy",  # Toggle between 'buy' or 'sell'.
        "order_type": "limit_order",  # Toggle between a 'market_order' or 'limit_order'.
        "market": "TLOSINR",  # Replace 'SNTBTC' with your desired market pair.
        "price_per_unit": 25.2115,  # This parameter is only required for a 'limit_order'
        "total_quantity": 7.93,  # Replace this with the quantity you want
        "timestamp": timeStamp,
    },
    "users_balance": {"timestamp": timeStamp},
    "exchange_ticker" : ""
}

url= {
    "orders_create" : "https://api.coindcx.com/exchange/v1/orders/create",
    "users_balance" : "https://api.coindcx.com/exchange/v1/users/balances",
    "exchange_ticker" : "https://api.coindcx.com/exchange/ticker",
    "user_data" : "https://api.coindcx.com/exchange/v1/users/info",
    "markets_details" : "https://api.coindcx.com/exchange/v1/markets_details",
    "get_candles" : "https://public.coindcx.com/market_data/candles?pair=B-BTC_USDT&interval=1m",
}

json_body = json.dumps(body, separators=(",", ":"))

secret_bytes = bytes(secret, encoding="UTF-8")

signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()


headers = {
    "Content-Type": "application/json",
    "X-AUTH-APIKEY": key,
    "X-AUTH-SIGNATURE": signature,
}


# Show the page title and description.
st.set_page_config(page_title="Crypto API Dashboard", page_icon="🍠",layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/dabhishek316",
        "Report a bug": "https://github.com/dabhishek316",
        "About": "# CoinDcx Trading App Bot!",
    },)
st.title("₿ Crypto API Dashboard")
st.write(
    """
    A Crypto API Dashboard is a platform designed to display  historical data about cryptocurrencies by integrating with cryptocurrency APIs and also provides some information regarding how to use crypto for trading using API using [CoinDcx App](https://coindcx.com/).
    """
)


# Load the data from a CSV. We're caching this so it doesn't reload every time the app
# reruns (e.g. if the user interacts with the widgets).
# @st.cache_data
# def load_data():
#     df = pd.read_csv("data/movies_genres_summary.csv")
#     return df


# df = load_data()

# # Show a multiselect widget with the genres using `st.multiselect`.
# genres = st.multiselect(
#     "Genres",
#     df.genre.unique(),
#     ["Action", "Adventure", "Biography", "Comedy", "Drama", "Horror"],
# )

# # Show a slider widget with the years using `st.slider`.
# years = st.slider("Years", 1986, 2006, (2000, 2016))

# # Filter the dataframe based on the widget input and reshape it.
# df_filtered = df[(df["genre"].isin(genres)) & (df["year"].between(years[0], years[1]))]
# df_reshaped = df_filtered.pivot_table(
#     index="year", columns="genre", values="gross", aggfunc="sum", fill_value=0
# )
# df_reshaped = df_reshaped.sort_values(by="year", ascending=False)


# # Display the data as a table using `st.dataframe`.
# st.dataframe(
#     df_reshaped,
#     use_container_width=True,
#     column_config={"year": st.column_config.TextColumn("Year")},
# )

# Display the data as an Altair chart using `st.altair_chart`.
# df_chart = pd.melt(
#     df_reshaped.reset_index(), id_vars="year", var_name="genre", value_name="gross"
# )
# chart = (
#     alt.Chart(df_chart)
#     .mark_line()
#     .encode(
#         x=alt.X("year:N", title="Year"),
#         y=alt.Y("gross:Q", title="Gross earnings ($)"),
#         color="genre:N",
#     )
#     .properties(height=320)
# )
# st.altair_chart(chart, use_container_width=True)



my_balance, market_data, user_data,candles  = st.tabs(["My Balance", "Market Data", "User Data", "Candles"])
with my_balance:
    st.subheader("My Balance", divider=True)
    def user_balance(st, requests, pd, url , body):
        st.button("Refresh Balance Data",use_container_width=True)
        with st.empty():
            response = requests.post(url, data = json_body, headers = headers)
            data = response.json()
            final=[]
            for d in  data:
                if d['balance'] > 0 or d['locked_balance'] > 0:
                    final.append(d)
            df = pd.DataFrame(final)
            df[['balance', 'locked_balance']].apply(pd.to_numeric)
            df = df[["currency", "locked_balance", "balance"]]
            
            df.sort_values(by="balance", ascending=False, inplace=True)
            df.index = range(1, len(df) + 1)
            st.write(df,use_container_width=True)
    user_balance(st, requests, pd, url["users_balance"], body["users_balance"])

with market_data:
    st.subheader("Market Data", divider=True)
    def get_exchange_coin_info(st, requests, pd, url , body):
        st.button("Refresh Market Data",use_container_width=True)
        with st.empty():
            response = requests.get(url)
            df = pd.DataFrame(response.json())
            # st.write(response.json())
            df[['ask', 'bid']] = df[['ask', 'bid']].apply(pd.to_numeric)
            df["ask_bid_difference"] = df["ask"]- df["bid"]
            df["ask_bid_per_difference"] = (df["ask_bid_difference"]/((df["ask"]+df["bid"])/2))*100
            df = df[df["market"].str.contains('INR', na=False)]
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True).dt.tz_convert('Asia/Kolkata')
            df.sort_values(by="ask_bid_per_difference", ascending=False, inplace=True)
            df.index = range(1, len(df) + 1)
            
            st.dataframe(df, use_container_width=True,key="dataframe")
    get_exchange_coin_info(st, requests, pd, url["exchange_ticker"], body["exchange_ticker"])

with candles:
    st.subheader("Candles", divider=True)
    def get_candles(st, requests, pd, url , body=None):
        st.button("Refresh Candles Data",use_container_width=True)
        with st.empty():
            response = requests.get(url["markets_details"])
            df_market = pd.DataFrame(response.json())
            df_market = df_market[df_market["base_currency_short_name"].str.contains('INR', na=False)]["pair"]
            # st.dataframe(df_market, use_container_width=True,key="dataframe")
            df_candle=pd.DataFrame()
            # for x in df_market:
            pair = "I-ETH_INR"
            interval = "1m"
            response2 = requests.get(f"https://public.coindcx.com/market_data/candles?pair={pair}&interval={interval}")

            df_candle = pd.DataFrame(response2.json())
            df_candle['time'] = pd.to_datetime(df_candle['time'], unit='ms', utc=True).dt.tz_convert('Asia/Kolkata')
                # st.write(df_market)
            st.dataframe(df_candle, use_container_width=True,key="dataframe")
    get_candles(st, requests, pd, url)

with user_data:
    def User_data(st, requests, pd, url , body):
        row = st.container()
        with row:
            response = requests.post(url, data = json_body, headers = headers)
            data = response.json()
            st.text("coindcx_id : " + data["coindcx_id"])
            st.text("first_name : " + data["first_name"])
            st.text("last_name : " + data["last_name"])
            st.text("mobile_number : " + data["mobile_number"])
            st.text("email : " + data["email"])
    User_data(st, requests, pd, url["user_data"], body["users_balance"])