
# 🟢 Day6：策略适配性深度分析 + 行情分类复盘
# 本日核心任务
# 拆解 2024–2025 行情结构，解释「持有赚钱、策略巨亏」的底层原因
# 量化统计：多空持仓时长、无效交叉次数
# 明确：双均线策略 适用 / 不适用 场景
# 给出改良方向，为 Day7 总结收尾

# 对你实测数据的精准复盘（关键）
# 你当前真实数据：
# 持有收益：+27.04%
# 策略收益：-14.45%
# 持有最大回撤：-16.52%
# 策略最大回撤：-23.48%
# 1. 核心原因拆解
# 本区间是 震荡慢牛行情
# 整体重心缓慢上移，但中途反复上下震荡、均线频繁缠绕。
# 双均线致命弱点：
# 上涨初期：信号滞后 → 踏空主升浪
# 短期回调：频繁假金叉 → 抄底被套
# 小反弹立刻死叉 → 卖在低位、买在高位
# 最终结果：
# 不吃大行情，只吃反复来回的亏损，风险反而更高。
# 2. 双均线「适用 / 不适用」清单
# ✅ 适合用双均线
# 单边上涨牛市
# 单边下跌熊市
# 趋势清晰、波动流畅的标的
# ❌ 绝对不适合
# 震荡市、横盘拉锯
# 银行 / 蓝筹长期慢牛、波动平缓
# 小级别反复来回震荡的标的
# 3. 重要量化认知
# 策略没有好坏，只有适配
# 震荡行情里：少交易 = 少亏钱
# 趋势策略的天敌：频繁震荡、无效交叉

import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt

# Mac 中文不乱码
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

bs.login()

# 区间：2024-01-01 ~ 2025-01-01
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

# 双均线
df["ma20"] = df["close"].rolling(20).mean()
df["ma60"] = df["close"].rolling(60).mean()

# 交易信号
df["signal"] = (df["ma20"] > df["ma60"]).astype(int)
df["daily_return"] = df["close"].pct_change()
df["strategy_return"] = df["signal"].shift(1) * df["daily_return"]

# 累计净值
df["cum_hold"] = (1 + df["daily_return"]).cumprod()
df["cum_strategy"] = (1 + df["strategy_return"]).cumprod()

# 最大回撤计算
df["hold_max"] = df["cum_hold"].cummax()
df["hold_dd"] = df["cum_hold"] / df["hold_max"] - 1

df["strategy_max"] = df["cum_strategy"].cummax()
df["strategy_dd"] = df["cum_strategy"] / df["strategy_max"] - 1

# ========== Day6 新增：行情&持仓统计 ==========
total_days = len(df)
hold_days = df["signal"].sum()
cash_days = total_days - hold_days
hold_ratio = hold_days / total_days

# 均线交叉次数
df["ma_diff"] = df["ma20"] - df["ma60"]
df["cross"] = df["ma_diff"].shift(1) * df["ma_diff"]
cross_times = (df["cross"] < 0).sum()

# 核心指标
hold_ret = df["cum_hold"].iloc[-1] - 1
sty_ret = df["cum_strategy"].iloc[-1] - 1
hold_dd_min = df["hold_dd"].min()
sty_dd_min = df["strategy_dd"].min()

# 绘图
plt.figure(figsize=(14,7))
plt.plot(df["cum_hold"], label="Buy&Hold 长期持有", linewidth=2)
plt.plot(df["cum_strategy"], label="MA20/MA60 双均线策略", linewidth=2)
plt.title("Day6：行情适配性复盘 | 震荡慢牛环境策略表现")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# 输出完整复盘报告
print("=" * 70)
print("📈 Day6 行情&策略全面复盘报告")
print(f"总交易日数：{total_days} 天")
print(f"策略持仓天数：{hold_days} 天 | 空仓天数：{cash_days} 天")
print(f"持仓占比：{hold_ratio:.1%}")
print(f"一年之内均线交叉反转次数：{cross_times} 次")
print("-" * 70)
print(f"全程持有总收益：{hold_ret:.2%}")
print(f"双均线策略总收益：{sty_ret:.2%}")
print(f"持有最大回撤：{hold_dd_min:.2%}")
print(f"策略最大回撤：{sty_dd_min:.2%}")
print("=" * 70)

bs.logout()