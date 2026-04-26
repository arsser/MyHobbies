# 🟢 Day4：双均线策略收益回测（看看策略到底赚不赚钱）
# Day4 核心目标
# 编写完整的双均线交易策略
# 计算策略收益 vs 持有不动收益
# 画出净值对比曲线
# 直观判断策略是否有效

# 📌 Day4 你会看到的结果
# 红色线 = 双均线策略
# 蓝色线 = 一直持有不动
# 图表标题会直接显示两个收益率
# 一目了然：策略有没有跑赢持有
# ✅ Day4 完成标准
# 运行后：
# 出现两条净值曲线
# 显示百分比收益
# 能看出策略是否更优


import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt

# Mac 无乱码字体
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 登录
bs.login()

# 获取近1年数据
rs = bs.query_history_k_data_plus(
    code="sz.000001",
    fields="date,close",
    start_date="2024-01-01",
    end_date="2025-01-01",
    frequency="d",
    adjustflag="3"
)
df = rs.get_data()

# 数据处理
df["date"] = pd.to_datetime(df["date"])
df["close"] = pd.to_numeric(df["close"])
df = df.set_index("date")

# 均线
df["ma20"] = df["close"].rolling(20).mean()
df["ma60"] = df["close"].rolling(60).mean()

# ======================
# Day4 核心：策略回测
# 1=持仓, 0=空仓
# ======================
df["signal"] = (df["ma20"] > df["ma60"]).astype(int)

# 计算每日涨跌幅
df["daily_return"] = df["close"].pct_change()

# 策略收益：信号 * 涨跌幅
df["strategy_return"] = df["signal"].shift(1) * df["daily_return"]

# 累计收益（净值曲线）
df["cum_hold"] = (1 + df["daily_return"]).cumprod()
df["cum_strategy"] = (1 + df["strategy_return"]).cumprod()

# 最终收益率
hold_final = df["cum_hold"].iloc[-1] - 1
strategy_final = df["cum_strategy"].iloc[-1] - 1

# 画图对比
plt.figure(figsize=(14, 7))
plt.plot(df["cum_strategy"], label="Strategy 双均线策略", linewidth=2, color="#e63946")
plt.plot(df["cum_hold"], label="Hold 持有不动", linewidth=2, color="#1d3557")
plt.title(f"Day4：策略收益对比\n持有收益：{hold_final:.1%} | 策略收益：{strategy_final:.1%}")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# 输出结果
print("="*50)
print("📊 Day4 回测结果")
print(f"持有不动收益：{hold_final:.1%}")
print(f"双均线策略收益：{strategy_final:.1%}")
print("="*50)

bs.logout()