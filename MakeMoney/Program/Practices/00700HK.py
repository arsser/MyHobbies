from openbb import obb  # type: ignore[reportMissingImports]
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ======================
# 腾讯港股（本地免费获取）
# ======================
ticker = "0700.HK"  # 腾讯控股
start_date = "2020-01-01"
end_date = "2025-01-01"

# 通过 OpenBB 获取历史行情（底层使用 yfinance provider）
df = obb.equity.price.historical(
    ticker,
    start_date=start_date,
    end_date=end_date,
    provider="yfinance",
).to_df()

if df.empty:
    raise RuntimeError("OpenBB 未返回有效数据，请检查网络或稍后重试。")

# 统一列名，兼容不同 provider 的字段大小写
df.columns = [str(col).lower() for col in df.columns]
if "close" not in df.columns:
    raise RuntimeError(f"返回数据不含 close 列，当前列为：{list(df.columns)}")
df["Close"] = df["close"]

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
plt.title("腾讯控股 0700.HK 双均线策略")
plt.legend()
plt.show()