# 1. 导入 openbb 包
from openbb import obb

# 2. 获取苹果公司(AAPL)从2023年至今的日线历史股价数据
# to_df() 是为了将数据转换为易于操作的 pandas DataFrame
stock_data = obb.equity.price.historical("AAPL", start_date="2023-01-01").to_df()

# 3. 打印数据
print(stock_data.head()) # 打印前5行
print(stock_data.tail()) # 打印后5行
