import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt

# Mac 中文渲染稳定配置
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 数据源登录
bs.login()

# 统一复盘区间
rs = bs.query_history_k_data_plus(
    code="sz.000001",
    fields="date,close",
    start_date="2024-01-01",
    end_date="2025-01-01",
    frequency="d",
    adjustflag="3"
)
df = rs.get_data()

# 数据标准化
df["date"] = pd.to_datetime(df["date"])
df["close"] = pd.to_numeric(df["close"])
df = df.set_index("date")

# 基础指标：双均线
df["ma20"] = df["close"].rolling(20).mean()
df["ma60"] = df["close"].rolling(60).mean()

# 趋势 & 交易信号
df["trend"] = 1
df.loc[df["ma20"] < df["ma60"], "trend"] = -1
df["signal"] = (df["ma20"] > df["ma60"]).astype(int)

# 收益计算
df["daily_return"] = df["close"].pct_change()
df["strategy_return"] = df["signal"].shift(1) * df["daily_return"]

# 累计净值
df["cum_hold"] = (1 + df["daily_return"]).cumprod()
df["cum_strategy"] = (1 + df["strategy_return"]).cumprod()

# 最大回撤
df["hold_peak"] = df["cum_hold"].cummax()
df["strategy_peak"] = df["cum_strategy"].cummax()
df["hold_drawdown"] = df["cum_hold"] / df["hold_peak"] - 1
df["strategy_drawdown"] = df["cum_strategy"] / df["strategy_peak"] - 1

# 核心指标提取
hold_ret = df["cum_hold"].iloc[-1] - 1
sty_ret = df["cum_strategy"].iloc[-1] - 1
hold_dd = df["hold_drawdown"].min()
sty_dd = df["strategy_drawdown"].min()

# 绘图总览
plt.figure(figsize=(14, 7))
plt.plot(df["cum_hold"], label="长期持有", linewidth=2)
plt.plot(df["cum_strategy"], label="MA20/MA60 双均线策略", linewidth=2)
plt.title("Day7｜7天量化学习 · 最终复盘总览")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# 终极总结报告
print("=" * 80)
print("📚 七天本地量化实战 · 最终复盘报告")
print("=" * 80)
print(f"标的：平安银行 sz.000001｜周期：2024.01.01–2025.01.01")
print(f"1. 全程持有总收益：{hold_ret:.2%}")
print(f"2. 双均线策略总收益：{sty_ret:.2%}")
print(f"3. 持有最大回撤：{hold_dd:.2%}")
print(f"4. 策略最大回撤：{sty_dd:.2%}")
print("=" * 80)

bs.logout()