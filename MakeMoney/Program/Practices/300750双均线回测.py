import akshare as ak
import pandas as pd
import time
from pathlib import Path
from requests.exceptions import RequestException
import sys

# 行情参数
SYMBOL = "300750"
START_DATE = "20240101"
END_DATE = "20241031"
ADJUST = "qfq"

_SCRIPT_DIR = Path(__file__).resolve().parent
_CACHE_DIR = _SCRIPT_DIR / "cache"
_CACHE_FILE = _CACHE_DIR / f"{SYMBOL}_{ADJUST}_{START_DATE}_{END_DATE}.csv"

# 腾讯 / 网易等接口需要带市场前缀
def _ak_symbol_with_prefix(code: str) -> str:
    c = str(code)
    if c.startswith("6"):
        return f"sh{c}"
    if c.startswith(("0", "3")):
        return f"sz{c}"
    if c.startswith(("8", "4")):
        return f"bj{c}"
    return c


def standardize_ohlcv(df: pd.DataFrame | None) -> pd.DataFrame | None:
    """统一为列：date, open, high, low, close, volume(可选), amount(可选)"""
    if df is None or df.empty:
        return None
    out = df.copy()
    cn_map = {
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
        "成交额": "amount",
    }
    for old, new in cn_map.items():
        if old in out.columns and new not in out.columns:
            out = out.rename(columns={old: new})
    # 小写英列
    for c in list(out.columns):
        if isinstance(c, str) and c.lower() in ("open", "high", "low", "close", "volume", "amount", "date"):
            out = out.rename(columns={c: c.lower()})
    if "date" not in out.columns and out.index.name in ("日期", "date"):
        out = out.reset_index()
        if "日期" in out.columns:
            out = out.rename(columns={"日期": "date"})
    if "date" not in out.columns:
        return None
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"])
    m = (out["date"] >= pd.to_datetime(START_DATE, format="%Y%m%d")) & (
        out["date"] <= pd.to_datetime(END_DATE, format="%Y%m%d")
    )
    out = out.loc[m]
    if "open" in out.columns:
        out = out.sort_values("date").reset_index(drop=True)
    return out


def get_data_eastmoney_with_retry() -> pd.DataFrame | None:
    for retry in range(5):
        try:
            print(f"  第{retry + 1}次尝试（东方财富）...")
            if retry:
                time.sleep(min(2.0 * (2 ** (retry - 1)), 30.0))
            df = ak.stock_zh_a_hist(
                symbol=SYMBOL,
                period="daily",
                start_date=START_DATE,
                end_date=END_DATE,
                adjust=ADJUST,
            )
            out = standardize_ohlcv(df)
            if out is not None and not out.empty:
                return out
        except (RequestException, OSError) as e:
            print(f"  错误: {str(e)[:100]}")
        except Exception as e:
            print(f"  错误: {str(e)[:100]}")
    return None


def get_data_tencent_with_retry() -> pd.DataFrame | None:
    if not hasattr(ak, "stock_zh_a_hist_tx"):
        return None
    sym = _ak_symbol_with_prefix(SYMBOL)
    for retry in range(3):
        try:
            print(f"  第{retry + 1}次尝试（腾讯）...")
            if retry:
                time.sleep(2.0 * (retry + 1))
            # 当前 akshare 签名为 (symbol, start_date, end_date, adjust)，无 period
            df = ak.stock_zh_a_hist_tx(
                symbol=sym,
                start_date=START_DATE,
                end_date=END_DATE,
                adjust=ADJUST,
            )
            out = standardize_ohlcv(df)
            if out is not None and not out.empty:
                return out
        except TypeError as e:
            print(f"  错误(参数不兼容可升级 akshare): {str(e)[:100]}")
            return None
        except Exception as e:
            print(f"  错误: {str(e)[:100]}")
    return None


def get_data_163_with_retry() -> pd.DataFrame | None:
    if not hasattr(ak, "stock_zh_a_hist_163"):
        return None
    sym = _ak_symbol_with_prefix(SYMBOL)
    for retry in range(3):
        try:
            print(f"  第{retry + 1}次尝试（网易，不复权价）...")
            if retry:
                time.sleep(2.0 * (retry + 1))
            df = ak.stock_zh_a_hist_163(
                symbol=sym,
                start_date=START_DATE,
                end_date=END_DATE,
            )
            out = standardize_ohlcv(df)
            if out is not None and not out.empty:
                return out
        except Exception as e:
            print(f"  错误: {str(e)[:100]}")
    return None


def get_data_with_akshare_only() -> pd.DataFrame | None:
    methods = [
        ("东方财富", get_data_eastmoney_with_retry),
        ("腾讯财经", get_data_tencent_with_retry),
        ("网易财经", get_data_163_with_retry),
    ]
    for name, func in methods:
        print(f"\n📡 尝试 {name}...")
        df = func()
        if df is not None and not df.empty:
            print(f"✅ {name} 成功，共 {len(df)} 条")
            return df
    return None


def load_stock_df() -> pd.DataFrame:
    """先读缓存，再多数据源；仍失败时若有旧缓存则使用。"""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if _CACHE_FILE.exists():
        try:
            df = pd.read_csv(_CACHE_FILE)
            if not df.empty:
                print(f"✅ 从缓存加载：{_CACHE_FILE} (共{len(df)} 条)")
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                for col in ["open", "high", "low", "close"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                return df
        except OSError as e:
            print(f"缓存读取失败：{e}")

    print("\n🔄 从网络拉取行情（东方财富 / 腾讯 / 网易）...")
    stock_df = get_data_with_akshare_only()

    if stock_df is not None and not stock_df.empty:
        try:
            stock_df.to_csv(_CACHE_FILE, index=False)
            print(f"💾 已缓存：{_CACHE_FILE}")
        except OSError as e:
            print(f"缓存写入失败：{e}")
        return stock_df

    if _CACHE_FILE.exists():
        try:
            df = pd.read_csv(_CACHE_FILE)
            if not df.empty:
                print("⚠️ 在线全失败，使用已有缓存文件（可能为旧数据）。")
                return df
        except OSError:
            pass

    raise RuntimeError(
        "所有在线数据源均失败且无可用本地缓存。请检查网络/代理后重试，"
        f"或把行情 CSV 放到：{_CACHE_FILE}"
    )


# ---------------------- 主程序 ----------------------
try:
    print("=" * 60)
    print("股票回测程序 v2.0 (UV环境适配)")
    print("=" * 60)
    
    # 检查必要的包
    required_packages = ["akshare", "pandas"]
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️ 缺少必要的包: {missing_packages}")
        print("请运行以下命令安装:")
        for package in missing_packages:
            print(f"  uv add {package}")
        sys.exit(1)
    
    # 获取数据
    stock_df = load_stock_df()
    
    if stock_df.empty:
        raise ValueError("获取的数据为空")
    
    # 确保数据按日期排序
    stock_df = stock_df.sort_values("date").reset_index(drop=True)
    
    # 转换数据类型
    for col in ["open", "high", "low", "close"]:
        stock_df[col] = pd.to_numeric(stock_df[col], errors='coerce')
    
    # 删除NaN值
    stock_df = stock_df.dropna(subset=["close"])
    
    print(f"\n📊 数据概况：")
    print(f"  股票代码：{SYMBOL}")
    print(f"  起始日期：{stock_df['date'].iloc[0]}")
    print(f"  结束日期：{stock_df['date'].iloc[-1]}")
    print(f"  数据条数：{len(stock_df)}")
    print(f"  价格范围：{stock_df['close'].min():.2f} - {stock_df['close'].max():.2f}")
    
    # ---------------------- 技术指标计算 ----------------------
    stock_df["5日均线"] = stock_df["close"].rolling(window=5).mean()
    stock_df["20日均线"] = stock_df["close"].rolling(window=20).mean()
    
    # 金叉信号：5日线上穿20日线
    stock_df["金叉信号"] = (stock_df["5日均线"].shift(1) < stock_df["20日均线"].shift(1)) & \
                          (stock_df["5日均线"] > stock_df["20日均线"])
    
    # 死叉信号：5日线下穿20日线
    stock_df["死叉信号"] = (stock_df["5日均线"].shift(1) > stock_df["20日均线"].shift(1)) & \
                          (stock_df["5日均线"] < stock_df["20日均线"])
    
    stock_df["交易信号"] = 0
    stock_df.loc[stock_df["金叉信号"], "交易信号"] = 1
    stock_df.loc[stock_df["死叉信号"], "交易信号"] = -1
    
    # ---------------------- 回测交易 ----------------------
    initial_capital = 100000
    cash = initial_capital
    hold_shares = 0
    trades = []
    
    print(f"\n📈 回测交易记录：")
    print("-" * 60)
    
    for i in range(len(stock_df)):
        close_price = stock_df.iloc[i]["close"]
        signal = stock_df.iloc[i]["交易信号"]
        date = stock_df.iloc[i]["date"]
        
        # 跳过NaN值
        if pd.isna(close_price):
            continue
        
        # 买入信号
        if signal == 1 and hold_shares == 0:
            hold_shares = int(cash // close_price)
            if hold_shares > 0:
                cost = hold_shares * close_price
                cash -= cost
                trades.append({"日期": date, "类型": "买入", "价格": close_price, 
                              "数量": hold_shares, "金额": cost})
                print(f"  {date} 买入 {hold_shares}股，价格：{close_price:.2f}，金额：{cost:.2f}")
        
        # 卖出信号
        elif signal == -1 and hold_shares > 0:
            revenue = hold_shares * close_price
            cash += revenue
            trades.append({"日期": date, "类型": "卖出", "价格": close_price,
                          "数量": hold_shares, "金额": revenue})
            print(f"  {date} 卖出 {hold_shares}股，价格：{close_price:.2f}，金额：{revenue:.2f}")
            hold_shares = 0
    
    # 最终持仓估值
    final_value = cash + (hold_shares * stock_df.iloc[-1]["close"] if hold_shares else 0)
    total_return = final_value - initial_capital
    return_rate = (total_return / initial_capital) * 100
    
    # ---------------------- 输出结果 ----------------------
    print("\n" + "=" * 60)
    print("📊 回测结果")
    print("=" * 60)
    print(f"初始资金：{initial_capital:,.2f}")
    print(f"最终资产：{final_value:,.2f}")
    print(f"总盈亏：{total_return:,.2f}")
    print(f"收益率：{return_rate:.2f}%")
    
    # 计算年化收益率
    if len(stock_df) > 0:
        start_date = pd.to_datetime(stock_df['date'].iloc[0])
        end_date = pd.to_datetime(stock_df['date'].iloc[-1])
        days = (end_date - start_date).days
        if days > 0:
            years = days / 365.25
            annual_return = ((final_value / initial_capital) ** (1 / years) - 1) * 100
            print(f"年化收益率：{annual_return:.2f}%")
    
    # 统计信息
    print(f"\n📈 交易统计：")
    print(f"  交易次数：{len(trades)}")
    if len(trades) > 0:
        buy_count = len([t for t in trades if t['类型'] == '买入'])
        sell_count = len([t for t in trades if t['类型'] == '卖出'])
        print(f"  买入次数：{buy_count}")
        print(f"  卖出次数：{sell_count}")
    
    # 显示最后10行数据
    print(f"\n📋 最后10日数据：")
    display_df = stock_df[["date", "close", "5日均线", "20日均线", "交易信号"]].tail(10)
    display_df = display_df.round(2)
    print(display_df.to_string(index=False))
    
    print("\n✨ 回测完成！")
    
except Exception as e:
    print(f"\n❌ 程序执行失败：{e}")
    import traceback
    traceback.print_exc()
    print("\n💡 建议：")
    print("1. 检查网络连接")
    print("2. 确保已安装所需包：uv add akshare pandas numpy")
    print("3. 尝试更换股票代码（例如 '000001'）")
    print("4. 减少时间范围（例如从最近3个月开始）")