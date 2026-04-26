import baostock as bs
import pandas as pd

# 登录（无需注册，直接调用）
lg = bs.login()
print("登录状态:", lg.error_code, lg.error_msg)

# 获取A股日线数据（300750 宁德时代，创业板 -> sz.300750）
rs = bs.query_history_k_data_plus(
    code="sz.300750",
    fields="date,open,high,low,close,volume,amount",
    start_date="2024-01-01",
    end_date="2026-4-1",
    frequency="d",  # d=日线, 5=5分钟, 15=15分钟, 30=30分钟, 60=60分钟
    adjustflag="2",  # 1=不复权, 2=前复权, 3=后复权
)

# 转 DataFrame：baostock 需用 next + get_data，无 bs.get_data
rows: list = []
if rs.error_code != "0":
    print("query 失败:", rs.error_msg)
    bs.logout()
    raise SystemExit(1)
while rs.next():
    rows.append(rs.get_row_data())
stock_df = pd.DataFrame(rows, columns=rs.fields)
stock_df = stock_df.rename(
    columns={
        "date": "日期",
        "open": "开盘价",
        "high": "最高价",
        "low": "最低价",
        "close": "收盘价",
        "volume": "成交量",
        "amount": "成交额",
    }
)
stock_df[["开盘价","最高价","最低价","收盘价"]] = stock_df[["开盘价","最高价","最低价","收盘价"]].astype(float)
stock_df["成交量"] = stock_df["成交量"].astype(float)

# 退出登录
bs.logout()

# 均线策略（和你之前完全一致）
stock_df["5日均线"] = stock_df["收盘价"].rolling(window=5).mean()
stock_df["20日均线"] = stock_df["收盘价"].rolling(window=20).mean()
stock_df["金叉信号"] = (stock_df["5日均线"].shift(1) < stock_df["20日均线"].shift(1)) & (stock_df["5日均线"] > stock_df["20日均线"])
stock_df["死叉信号"] = (stock_df["5日均线"].shift(1) > stock_df["20日均线"].shift(1)) & (stock_df["5日均线"] < stock_df["20日均线"])
stock_df["交易信号"] = 0
stock_df.loc[stock_df["金叉信号"], "交易信号"] = 1
stock_df.loc[stock_df["死叉信号"], "交易信号"] = -1

# 回测
cash = 100000
hold_shares = 0
for i in range(len(stock_df)):
    close = stock_df.iloc[i]["收盘价"]
    signal = stock_df.iloc[i]["交易信号"]
    if signal == 1 and hold_shares == 0:
        hold_shares = cash // close
        cash -= hold_shares * close
        print(f"{stock_df.iloc[i]['日期']} 买入：{close:.2f}")
    elif signal == -1 and hold_shares > 0:
        cash += hold_shares * close
        hold_shares = 0
        print(f"{stock_df.iloc[i]['日期']} 卖出：{close:.2f}")

final = cash + (hold_shares * stock_df.iloc[-1]["收盘价"] if hold_shares else 0)
print(f"\n初始：100000，最终：{final:.2f}，收益率：{(final-100000)/1000:.2f}%")