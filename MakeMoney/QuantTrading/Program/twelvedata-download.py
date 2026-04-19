import os

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TWELVEDATA_API_KEY")
if not API_KEY:
    raise ValueError("请在 .env 中设置 TWELVEDATA_API_KEY")

url = "https://api.twelvedata.com/time_series"

params = {
    "symbol": "AAPL",
    "interval": "1day",
    "apikey": API_KEY,
    "outputsize": 5000,   # 免费版允许最大值，覆盖5000交易日
    "format": "JSON"
}

response = requests.get(url, params=params)
data = response.json()

# 检查是否出现错误
if "values" not in data:
    print("Error:", data)
else:
    df = pd.DataFrame(data["values"])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values("datetime")  # 时间顺序排序

    print(df.head())
    print(df.tail())

    # 保存成 CSV
    df.to_csv("AAPL_5year_twelvedata.csv", index=False)
    print("数据已保存为 AAPL_5year_twelvedata.csv")