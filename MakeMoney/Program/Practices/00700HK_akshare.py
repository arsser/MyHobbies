import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ======================
# 腾讯港股（AKShare 数据源）
# ======================
symbol = "00700"
start_date = "20200101"
end_date = "20250101"

# 获取港股历史行情（日线）
df = ak.stock_hk_hist(
    symbol=symbol,
    period="daily",
    start_date=start_date,
    end_date=end_date,
    adjust="",
)

if df.empty:
    raise RuntimeError("AKShare 未返回有效数据，请检查网络或稍后重试。")

# 统一字段，便于后续计算和画图
column_map = {
    "日期": "Date",
    "开盘": "Open",
    "收盘": "Close",
    "最高": "High",
    "最低": "Low",
    "成交量": "Volume",
}
df = df.rename(columns=column_map)

required_cols = {"Date", "Close"}
if not required_cols.issubset(df.columns):
    raise RuntimeError(f"返回数据缺少关键列，当前列为：{list(df.columns)}")

df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").set_index("Date")

# 计算双均线
df["MA20"] = df["Close"].rolling(window=20).mean()
df["MA60"] = df["Close"].rolling(window=60).mean()

# 打印最近10条数据
print(df.tail(10))

# 画图
plt.figure(figsize=(16, 6))
plt.plot(df["Close"], label="腾讯收盘价")
plt.plot(df["MA20"], label="MA20")
plt.plot(df["MA60"], label="MA60")
plt.title("腾讯控股 00700.HK 双均线策略（AKShare）")
plt.legend()
plt.tight_layout()
plt.show()
