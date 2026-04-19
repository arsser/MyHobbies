import os

from dotenv import load_dotenv
from twelvedata import TDClient

load_dotenv()
api_key = os.getenv("TWELVEDATA_API_KEY")
if not api_key:
    raise ValueError("请在 .env 中设置 TWELVEDATA_API_KEY")

td = TDClient(apikey=api_key)

# 拿到某支股票 1 分钟线，最近 500 条数据
df = td.time_series(symbol="AAPL", interval="1min", outputsize=500).as_pandas()

# 加入技术指标，例如 MACD + 布林带 + EMA
df2 = (
    td.time_series(symbol="AAPL", interval="1day", outputsize=365)
    .with_macd()
    .with_bbands(ma_type="EMA")
    .with_ema(time_period=20)
    .as_pandas()
)
