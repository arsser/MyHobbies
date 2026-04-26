# 标的：A 股 平安银行（000001.SZ）
# 数据源：BaoStock（本地 Python，无优矿）
# Day2 核心目标
# 学会用 MA20、MA60 识别趋势
# 区分：上涨趋势 / 下跌趋势
# 看懂均线之间的关系
# 输出带趋势判断的数据

# 📌 Day2 你必须看懂的规则
# MA20 在 MA60 上面 = 上涨趋势
# MA20 在 MA60 下面 = 下跌趋势
# 两条线交叉 = 趋势反转

# ✅ Day2 完成标准
# 运行后：
# 图表正常显示
# 输出最近 10 天数据
# 你能看懂 trend 列是上涨还是下跌

import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt

# ======================
# Mac 字体（无乱码版）
# ======================
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 登录 BaoStock
bs.login()

# 获取数据
rs = bs.query_history_k_data_plus(
    code="sz.000001",
    fields="date,close",
    start_date="2023-01-01",
    end_date="2025-01-01",
    frequency="d",
    adjustflag="3"
)
df = rs.get_data()

# 数据清洗
df["date"] = pd.to_datetime(df["date"])
df["close"] = pd.to_numeric(df["close"])
df = df.set_index("date")

# 计算均线
df["ma20"] = df["close"].rolling(20).mean()
df["ma60"] = df["close"].rolling(60).mean()

# ======================
# Day2 核心：判断趋势
# 规则：
# MA20 > MA60 → 上涨趋势 (1)
# MA20 < MA60 → 下跌趋势 (-1)
# ======================
df["trend"] = 0  # 初始化
df.loc[df["ma20"] > df["ma60"], "trend"] = 1
df.loc[df["ma20"] < df["ma60"], "trend"] = -1

# 画图：价格 + 均线 + 趋势
plt.figure(figsize=(14, 7))
plt.plot(df["close"], label="Close Price", color="#333")
plt.plot(df["ma20"], label="MA20", color="#ff9900")
plt.plot(df["ma60"], label="MA60", color="#0099ff")
plt.title("Day2: Trend by MA20 & MA60")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# ======================
# 输出最近10天趋势
# 1=上涨趋势
# -1=下跌趋势
# ======================
print("=== Day2 最近10天趋势 ===")
print(df[["close", "ma20", "ma60", "trend"]].tail(10))

bs.logout()