# 四、复盘结论怎么看（对照你之前的亏损）
# 输出里 shock 天数越多
# → 区间内震荡越严重 → 双均线必然拉胯
# up_trend 天数少
# → 真正主升浪很短，策略踏空
# 震荡期日均收益弱、反复波动
# → 假金叉密集，频繁小亏累加
# 对应你现实结果
# 持有躺赢：+27.04%
# 均线择时：-14.45%
# 本质：大部分时间是震荡行情，策略完全水土不服。

import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.unicode_minus'] = False

bs.login()
rs = bs.query_history_k_data_plus(
    code="sz.000001",
    fields="date,close",
    start_date="2024-01-01",
    end_date="2025-01-01",
    frequency="d",
    adjustflag="3"
)
df = rs.get_data()

df["date"] = pd.to_datetime(df["date"])
df["close"] = pd.to_numeric(df["close"])
df = df.set_index("date")

# 双均线
df["ma20"] = df["close"].rolling(20).mean()
df["ma60"] = df["close"].rolling(60).mean()

# ========== 行情分类核心逻辑 ==========
# 1. 计算MA60斜率（20日斜率，判断中期方向）
df["ma60_slope"] = df["ma60"].diff(20) / df["ma60"].shift(20)
# 2. 均线偏离度
df["ma_diff_rate"] = (df["ma20"] - df["ma60"]) / df["ma60"]

# 3. 行情分类打标
def label_market(row):
    slope = row["ma60_slope"]
    diff = row["ma_diff_rate"]
    if pd.isna(slope) or pd.isna(diff):
        return "none"
    # 趋势上涨
    if slope > 0.03 and diff > 0:
        return "up_trend"
    # 趋势下跌
    elif slope < -0.03 and diff < 0:
        return "down_trend"
    # 震荡
    else:
        return "shock"

df["market_type"] = df.apply(label_market, axis=1)
# ======================================

# 统计各类行情天数
cnt = df["market_type"].value_counts()
print("==== 行情分类统计复盘 ====")
print(cnt)

# 分段收益拆解
df["return"] = df["close"].pct_change()
group_ret = df.groupby("market_type")["return"].mean()
print("\n==== 不同行情日均收益 ====")
print(group_ret)

bs.logout()