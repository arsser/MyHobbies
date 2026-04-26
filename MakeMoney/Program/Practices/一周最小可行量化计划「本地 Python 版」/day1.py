
# Day1 验收标准（你必须看到）
# 运行无任何报错
# 弹出一张带日期、带中文、带三条线的图
# 终端输出最近 10 天数据
# 环境干净、无内存限制、无平台限制


import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt

# Day1：A股 平安银行（000001.SZ），BaoStock原生支持
bs.login()

# A股正确格式：sz.000001（深交所）、sh.600000（上交所）
rs = bs.query_history_k_data_plus(
    code="sz.000001",
    fields="date,close",
    start_date="2023-01-01",
    end_date="2025-01-01",
    frequency="d",
    adjustflag="3"  # 后复权
)
df = rs.get_data()

# 数据处理（现在一定有date列）
df["date"] = pd.to_datetime(df["date"])
df["close"] = pd.to_numeric(df["close"])
df = df.set_index("date")

# 均线
df["ma20"] = df["close"].rolling(20).mean()
df["ma60"] = df["close"].rolling(60).mean()

# ======================
# 【仅修改这里：Mac 专用字体，解决乱码】
# ======================
plt.rcParams["font.sans-serif"] = ["Heiti TC", "PingFang HK", "STHeiti", "Songti SC", "Arial Unicode MS"]  # 增加备选字体
plt.rcParams["axes.unicode_minus"] = False

plt.figure(figsize=(14,6))
plt.plot(df["close"], label="平安银行收盘价")
plt.plot(df["ma20"], label="MA20")
plt.plot(df["ma60"], label="MA60")
plt.title("Day1：A股 平安银行 双均线")
plt.legend()
plt.grid(True)
plt.show()

print("✅ Day1 A股版运行成功")
print(df.tail())
bs.logout()