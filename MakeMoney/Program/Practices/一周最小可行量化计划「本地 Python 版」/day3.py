# Day3：金叉 / 死叉自动识别（趋势交易核心信号）
# Day3 核心目标
# 学会金叉（买入信号）、死叉（卖出信号）
# 代码自动识别历史所有交叉点
# 统计总共有多少次金叉、多少次死叉
# 在图表上直观看到信号位置

# 📌 Day3 你必须看懂的规则
# 红色点 = 金叉
# MA20 从下往上穿 MA60 → 趋势由弱变强
# 绿色点 = 死叉
# MA20 从上往下穿 MA60 → 趋势由强变弱
这就是趋势策略最核心的买卖信号

# ✅ Day3 完成标准
# 运行后你会看到：
# 图表上出现红色 / 绿色信号点
# 标题显示金叉、死叉总次数
# 终端输出最近数据

import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Mac 字体（无乱码）
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 登录数据接口
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

# 数据清洗
df["date"] = pd.to_datetime(df["date"])
df["close"] = pd.to_numeric(df["close"])
df = df.set_index("date")

# 计算均线
df["ma20"] = df["close"].rolling(20).mean()
df["ma60"] = df["close"].rolling(60).mean()

# ======================
# Day3 核心：金叉、死叉
# 金叉 = MA20 上穿 MA60 → 1
# 死叉 = MA20 下穿 MA60 → -1
# ======================
df['ma20_prev'] = df['ma20'].shift(1)
df['ma60_prev'] = df['ma60'].shift(1)

# 金叉信号
df['golden_cross'] = np.where(
    (df['ma20_prev'] < df['ma60_prev']) & (df['ma20'] > df['ma60']),
    df['close'], np.nan
)

# 死叉信号
df['dead_cross'] = np.where(
    (df['ma20_prev'] > df['ma60_prev']) & (df['ma20'] < df['ma60']),
    df['close'], np.nan
)

# 统计信号数量
gold_count = df['golden_cross'].count()
dead_count = df['dead_cross'].count()

# 画图
plt.figure(figsize=(14, 7))
plt.plot(df["close"], label="Close Price", color="#555")
plt.plot(df["ma20"], label="MA20", color="#ff9900")
plt.plot(df["ma60"], label="MA60", color="#0099ff")

# 标记信号
plt.scatter(df.index, df['golden_cross'], color='red', label='Golden Cross', s=80, zorder=5)
plt.scatter(df.index, df['dead_cross'], color='green', label='Dead Cross', s=80, zorder=5)

plt.title(f"Day3: Golden Cross & Dead Cross | 金叉:{gold_count} 次  死叉:{dead_count} 次")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# 输出最近信号
print("=== 最近 10 天信号（金叉=红色点，死叉=绿色点）===")
print(df[['close', 'ma20', 'ma60']].tail(10))
print(f"\n✅ 总计：金叉 {gold_count} 次，死叉 {dead_count} 次")

bs.logout()