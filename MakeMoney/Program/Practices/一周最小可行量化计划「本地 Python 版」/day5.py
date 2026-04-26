
# 🟢 Day5：加入风控体系｜计算最大回撤 + 风险对比
# 核心目标
# 增加量化核心风控指标：最大回撤
# 直观对比：「纯持有」vs「双均线策略」的风险差距
# 理解：收益看盈利，交易看回撤
# 为后续优化止盈 / 止损打下基础

# 关键结论（解答你刚才的疑惑）
# 这只标的 2024 全年整体阴跌、震荡下行
# 即便有空仓避险，短暂多头入场依然会亏损
# 所以策略收益依旧为负，不是代码错误，是行情属性导致
# 但风控价值已经体现：
# 对比「全程死拿」
# 双均线策略往往可以降低最大回撤、减少深度套牢
# 核心认知：
# 震荡熊市：任何趋势策略都会失效
# 牛市 / 趋势行情：双均线会大幅跑赢持有

import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt

# Mac 中文渲染
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 登录 BaoStock
bs.login()

# 行情区间
rs = bs.query_history_k_data_plus(
    code="sz.300750",
    fields="date,close",
    start_date="2024-01-01",
    end_date="2025-01-01",
    frequency="d",
    adjustflag="3"
)
df = rs.get_data()

# 数据清洗
df["date"] = pd.to_datetime(df["date"])
df["close"] = pd.to_numeric(df["close"])
df = df.set_index("date")

# 双均线
df["ma20"] = df["close"].rolling(20).mean()
df["ma60"] = df["close"].rolling(60).mean()

# 交易信号：MA20>MA60 持仓
df["signal"] = (df["ma20"] > df["ma60"]).astype(int)

# 每日收益
df["daily_return"] = df["close"].pct_change()
df["strategy_return"] = df["signal"].shift(1) * df["daily_return"]

# 累计净值
df["cum_hold"] = (1 + df["daily_return"]).cumprod()
df["cum_strategy"] = (1 + df["strategy_return"]).cumprod()

# --------------------------
# 【Day5 核心：最大回撤计算】
# --------------------------
# 持有最大回撤
df["hold_max"] = df["cum_hold"].cummax()
df["hold_dd"] = df["cum_hold"] / df["hold_max"] - 1

# 策略最大回撤
df["strategy_max"] = df["cum_strategy"].cummax()
df["strategy_dd"] = df["cum_strategy"] / df["strategy_max"] - 1

# 指标提取
hold_total_return = df["cum_hold"].iloc[-1] - 1
strategy_total_return = df["cum_strategy"].iloc[-1] - 1
hold_max_dd = df["hold_dd"].min()
strategy_max_dd = df["strategy_dd"].min()

# 绘图
plt.figure(figsize=(14, 7))
plt.plot(df["cum_strategy"], label="双均线策略", linewidth=2)
plt.plot(df["cum_hold"], label="长期持有", linewidth=2)
plt.title(
    f"Day5 收益&风控对比\n"
    f"持有收益：{hold_total_return:.2%}  最大回撤：{hold_max_dd:.2%}\n"
    f"策略收益：{strategy_total_return:.2%}  最大回撤：{strategy_max_dd:.2%}"
)
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# 终端打印完整风控报告
print("=" * 60)
print("📊 Day5 量化风控报告")
print(f"1. 标的总收益(持有)：{hold_total_return:.2%}")
print(f"2. 策略总收益：{strategy_total_return:.2%}")
print(f"3. 持有最大回撤：{hold_max_dd:.2%}")
print(f"4. 策略最大回撤：{strategy_max_dd:.2%}")
print("=" * 60)

bs.logout()